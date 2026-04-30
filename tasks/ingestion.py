"""Veri toplama (ingestion) gorevleri.

Bu gorevler APScheduler tarafindan tetiklenir.
Kullanici istekleri bu gorevleri ASLA tetiklemez (rules.md #1).

Pipeline: Client → Adapter → Repository → Cache Invalidation

Iki veri kaynagi:
  1. Odds API → Yaklasan maclar (otomatik, 17:00 + 21:00 TR)
  2. Football-data.co.uk CSV → Gecmis maclar (manuel, load_local.py)
"""

import asyncio
import glob
import logging
import os
from datetime import datetime, timedelta, timezone

from adapters.football_adapter import FootballAdapter
from clients.base_client import APIClientError, QuotaExhaustedError
from clients.odds_api_client import OddsAPIClient
from core.config import settings
from core.database import mongo
from core.redis_client import redis_manager
from utils.lock import distributed_lock

logger = logging.getLogger(__name__)

# Adapter registry
ADAPTERS = {
    "football": FootballAdapter(),
}

# Eger bir macin updated_at degeri bu sureden yeniyse tekrar cekilmez
SKIP_IF_FRESH_HOURS = 4


# ═══════════════════════════════════════════════
#  ODDS API — YAKLASAN MACLAR (OTOMATİK)
# ═══════════════════════════════════════════════


@distributed_lock("lock:ingestion:upcoming", timeout=900)
async def fetch_upcoming_matches() -> None:
    """The Odds API'den yaklasan maclari ceker ve DB'ye yazar (Dagitik kilit ile)."""
    try:
        logger.info("═══ YAKLASAN MACLARI CEKME BASLADI ═══")

        adapter = ADAPTERS.get("football")
        if not adapter:
            logger.error("Football adapter bulunamadi!")
            return

        client = OddsAPIClient()
        db = mongo.get_db()

        total_new = 0
        total_skipped = 0

        for league_key in settings.TARGET_LEAGUES:
            try:
                new, skipped = await _fetch_league(client, adapter, db, league_key)
                total_new += new
                total_skipped += skipped
            except QuotaExhaustedError:
                logger.error("API kota limiti asildi! Ingestion durduruluyor.")
                break
            except Exception as exc:
                logger.error("Lig [%s] hatasi: %s", league_key, exc)
                continue

        # Cache guncelle
        await _invalidate_cache("football")

        logger.info(
            "═══ GUNCELLEME TAMAMLANDI: %d yeni, %d atlandi ═══",
            total_new, total_skipped,
        )
    except Exception as exc:
        logger.error("Ingestion genel hatasi: %s", exc)
        raise


async def _fetch_league(
    client: OddsAPIClient,
    adapter: FootballAdapter,
    db,
    league_key: str,
) -> tuple[int, int]:
    """Tek bir lig icin yaklasan maclari ceker ve filtreler.
    
    Returns:
        (yeni_mac_sayisi, atlanan_mac_sayisi) tuple'i.
    """
    try:
        raw_events = await client.fetch_upcoming_odds(league_key)
    except APIClientError as exc:
        logger.warning("Lig [%s] icin veri cekilemedi: %s", league_key, exc)
        return (0, 0)

    if not raw_events:
        return (0, 0)

    # Adapter ile normalize et
    entities = adapter.normalize_upcoming(raw_events)
    
    if not entities:
        return (0, 0)

    # Zaten guncel olanlari filtrele (kota optimizasyonu)
    freshness_cutoff = datetime.now(timezone.utc) - timedelta(hours=SKIP_IF_FRESH_HOURS)
    entities_to_upsert = []
    skipped = 0

    for entity in entities:
        existing = await db.matches.find_one(
            {"external_id": entity.external_id},
            {"updated_at": 1}
        )
        
        if existing:
            existing_updated = existing.get("updated_at")
            if existing_updated and existing_updated.replace(tzinfo=timezone.utc) > freshness_cutoff:
                skipped += 1
                continue
        
        entities_to_upsert.append(entity)

    # Upsert
    if entities_to_upsert:
        await _upsert_to_db(entities_to_upsert)

    logger.info(
        "Lig [%s]: %d yeni/guncellenen, %d atlanan.",
        league_key, len(entities_to_upsert), skipped,
    )
    return (len(entities_to_upsert), skipped)


# ═══════════════════════════════════════════════
#  YARDIMCI FONKSIYONLAR
# ═══════════════════════════════════════════════


async def _upsert_to_db(entities: list) -> None:
    """MatchEntity listesini MongoDB'ye toplu upsert yapar."""
    from pymongo import UpdateOne

    db = mongo.get_db()
    operations = []

    def _get_docs(entities_list):
        return [e.model_dump() for e in entities_list]

    # Faz 6 Fix: Pydantic model_dump (CPU-intensive) thread'e alindi
    docs = await asyncio.to_thread(_get_docs, entities)

    for i, entity in enumerate(entities):
        operations.append(
            UpdateOne(
                {"external_id": entity.external_id},
                {"$set": docs[i]},
                upsert=True,
            )
        )

    if operations:
        result = await db.matches.bulk_write(operations, ordered=False)
        logger.info(
            "MongoDB upsert: %d eklendi, %d guncellendi.",
            result.upserted_count,
            result.modified_count,
        )


async def _invalidate_cache(sport_name: str) -> None:
    """Ilgili Redis cache anahtarlarini siler."""
    try:
        redis = redis_manager.get_client()
        pattern = f"matches:{sport_name}:*"
        keys = []
        async for key in redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await redis.delete(*keys)
            logger.info("Redis cache temizlendi: %d anahtar silindi.", len(keys))
    except Exception as exc:
        logger.warning("Redis cache temizleme hatasi: %s", exc)


# ═══════════════════════════════════════════════
#  TARIHSEL VERI YUKLEME (TEK SEFERLIK / MANUEL)
# ═══════════════════════════════════════════════


@distributed_lock("lock:ingestion:seed_historical", timeout=1800)
async def seed_historical_data() -> None:
    """data/ klasorundeki CSV dosyalarini MongoDB'ye yukler."""
    import csv as csv_module
    import aiofiles
    import io
    
    try:
        logger.info("═══ TARIHSEL VERI YUKLEME BASLADI ═══")

        adapter = ADAPTERS.get("football")
        if not adapter:
            logger.error("Football adapter bulunamadi!")
            return

        data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
        csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

        if not csv_files:
            logger.info("data/ klasorunde CSV dosyasi bulunamadi.")
            return

        total_count = 0

        for csv_path in csv_files:
            filename = os.path.basename(csv_path)
            league_code = filename.split("_")[0].split(".")[0]

            try:
                # Faz 6 Fix: Asenkron dosya okuma ve Senkron parsing thread'e alindi
                async with aiofiles.open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
                    content = await f.read()
                
                def _parse_csv(data: str):
                    reader = csv_module.DictReader(io.StringIO(data))
                    return list(reader)
                
                rows = await asyncio.to_thread(_parse_csv, content)

                if not rows:
                    continue

                entities = adapter.normalize_historical(rows, league_code=league_code)
                if entities:
                    await _upsert_to_db(entities)
                    total_count += len(entities)
                    logger.info("CSV yuklendi: %s → %d mac.", filename, len(entities))
            except Exception as exc:
                logger.error("CSV yukleme hatasi [%s]: %s", filename, exc, exc_info=True)
                continue

        # Cache temizle
        await _invalidate_cache("football")
        logger.info("═══ TARIHSEL VERI YUKLEME TAMAMLANDI: %d mac ═══", total_count)
    except Exception as exc:
        logger.error("Tarihsel veri yukleme hatasi: %s", exc)
        raise

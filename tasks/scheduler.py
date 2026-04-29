"""APScheduler yapilandirmasi.

Uygulama ayaga kalktiginda scheduler baslatilir.
Cron job'lar burada tanimlanir.

Zamanlamalar:
  - fetch_upcoming: TR 17:00 (UTC 14:00) ve TR 21:00 (UTC 18:00)
  - seed_historical: Uygulama basladiginda bir kez (10s sonra)
"""

import logging
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger

from core.config import settings

logger = logging.getLogger(__name__)

# Scheduler nesnesi — main.py lifespan'da start/stop edilir
scheduler = AsyncIOScheduler(timezone="UTC")


def configure_scheduler() -> None:
    """Zamanlanmis gorevleri kaydeder.

    1. fetch_upcoming_matches: Gunde 2 kez yaklasan mac oranlarini ceker.
    2. seed_historical_data: Uygulama ilk kez basladiginda CSV verilerini yukler.
    """
    from tasks.ingestion import fetch_upcoming_matches, seed_historical_data

    # Her slot icin ayri bir cron job olustur (TR 17:00 ve 21:00)
    for i, slot in enumerate(settings.SCHEDULER_SLOTS):
        job_id = f"fetch_upcoming_{i}"
        scheduler.add_job(
            fetch_upcoming_matches,
            trigger=CronTrigger(
                hour=slot["hour"],
                minute=slot["minute"],
            ),
            id=job_id,
            name=f"Yaklasan mac guncelleme @ {slot['hour']:02d}:{slot['minute']:02d} UTC",
            replace_existing=True,
            misfire_grace_time=3600,  # 1 saat tolerans
        )
        logger.info(
            "Cron job kayitli: %s @ %02d:%02d UTC (TR %02d:%02d)",
            job_id, slot["hour"], slot["minute"],
            slot["hour"] + 3, slot["minute"],  # UTC+3 = TR
        )

    # Tarihsel veri yukleme (bir kez, 10 saniye sonra)
    scheduler.add_job(
        seed_historical_data,
        trigger=DateTrigger(
            run_date=datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=10)
        ),
        id="seed_historical_data",
        name="Tarihsel CSV verisi yukleme (tek seferlik)",
        replace_existing=True,
    )
    logger.info("Tek seferlik job kayitli: seed_historical_data (10s sonra)")

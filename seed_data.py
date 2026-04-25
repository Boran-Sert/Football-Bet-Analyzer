"""data/ klasorundeki CSV dosyalarini MongoDB'ye aktaran seed scripti.

Kullanim:
    python scripts/seed_data.py

CSV'lerdeki gecmis mac verilerini matches koleksiyonuna yazar.
Boylece frontend'de analiz testi yapabilirsiniz.
"""

import asyncio
import csv
import os
import sys
from datetime import datetime

# Proje kokunu path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.database import mongo
from repositories.match_repository import MatchRepository

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Dosya adi → Lig adi eslesmesi
FILE_LEAGUE_MAP = {
    "T1": "Türkiye Süper Lig",
    "E0": "İngiltere Premier Lig",
    "SP1": "İspanya La Liga",
    "I1": "İtalya Serie A",
    "D1": "Almanya Bundesliga",
    "F1": "Fransa Ligue 1",
}


def _safe_float(val):
    """String degeri float'a cevirir, bossa None doner."""
    if val is None or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _safe_int(val):
    """String degeri int'e cevirir, bossa None doner."""
    if val is None or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _parse_date(date_str):
    """Tarih stringini datetime objesine cevirir."""
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def _detect_league_and_season(filename):
    """Dosya adindan lig kodu ve sezonu cikarir.

    Ornekler:
        T1_2024-2025.csv → ("Türkiye Süper Lig", "2024-2025")
        E0_2023-2024.csv → ("İngiltere Premier Lig", "2023-2024")
        2024-2025.csv    → (None, "2024-2025")
    """
    name = filename.replace(".csv", "")
    parts = name.split("_")

    if len(parts) == 2:
        code, season = parts
        league = FILE_LEAGUE_MAP.get(code)
        return league, season
    elif len(parts) == 1 and "-" in parts[0]:
        return None, parts[0]

    return None, None


async def seed_csv(filepath, league, season, repo):
    """Tek bir CSV dosyasini MongoDB'ye aktarir."""
    inserted = 0

    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            match_date = _parse_date(row.get("Tarih", ""))
            if not match_date:
                continue

            home = row.get("Ev Sahibi", "").strip()
            away = row.get("Deplasman", "").strip()
            if not home or not away:
                continue

            hg = _safe_int(row.get("Ev Sahibi Gol"))
            ag = _safe_int(row.get("Deplasman Gol"))

            doc = {
                "home_team": home,
                "away_team": away,
                "league": league or "Bilinmeyen Lig",
                "season": season or "unknown",
                "match_date": match_date,
                "home_goals": hg,
                "away_goals": ag,
                "odds_home": _safe_float(row.get("MS 1")),
                "odds_draw": _safe_float(row.get("MS 0")),
                "odds_away": _safe_float(row.get("MS 2")),
                "odds_over_25": _safe_float(row.get("2.5 Ust")),
                "odds_under_25": _safe_float(row.get("2.5 Alt")),
                "status": "finished" if hg is not None else "scheduled",
            }

            await repo.upsert_match(doc)
            inserted += 1

    return inserted


async def main():
    """Tum CSV dosyalarini tarar ve MongoDB'ye yazar."""
    await mongo.connect()
    print("✅ MongoDB baglantisi kuruldu.\n")

    repo = MatchRepository(mongo.db)

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not csv_files:
        print("❌ data/ klasorunde CSV dosyasi bulunamadi.")
        return

    total = 0
    for filename in sorted(csv_files):
        filepath = os.path.join(DATA_DIR, filename)
        league, season = _detect_league_and_season(filename)

        print(f"📂 {filename}")
        print(f"   Lig: {league or '?'}  |  Sezon: {season or '?'}")

        count = await seed_csv(filepath, league, season, repo)
        total += count
        print(f"   ✅ {count} mac eklendi/guncellendi.\n")

    print(f"🏁 Toplam: {total} mac MongoDB'ye aktarildi.")

    await mongo.close()


if __name__ == "__main__":
    asyncio.run(main())

"""APScheduler yapilandirmasi.

AsyncIOScheduler kullanarak arka plan gorevlerini
belirlenen saatlerde calistirir.
rules.md Madde 1: Dis API cagrisi sadece tasks/ icerisindeki cron job'larla yapilir.
"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from tasks.fetch_data import fetch_daily_matches

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def configure_scheduler() -> None:
    """Zamanlayiciyi yapilandirir. Henuz baslatmaz (start icin lifespan kullan)."""

    # Her gun 17:00 (Turkiye saati) → Aksam maclari oncesi veri guncelle
    scheduler.add_job(
        fetch_daily_matches,
        trigger=CronTrigger(hour=17, minute=0, timezone="Europe/Istanbul"),
        id="fetch_matches_17",
        name="Gunluk mac verisi guncelleme (17:00)",
        replace_existing=True,
    )

    # Her gun 21:00 (Turkiye saati) → Aksam maclari oranlarini guncelle
    scheduler.add_job(
        fetch_daily_matches,
        trigger=CronTrigger(hour=21, minute=0, timezone="Europe/Istanbul"),
        id="fetch_matches_21",
        name="Gunluk mac verisi guncelleme (21:00)",
        replace_existing=True,
    )

    logger.info("Scheduler yapilandirildi: 17:00 ve 21:00 (Europe/Istanbul)")

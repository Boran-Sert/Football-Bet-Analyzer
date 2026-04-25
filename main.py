"""FastAPI uygulama giris noktasi.

Lifespan context manager ile uygulama baslarken:
  - MongoDB baglanir
  - Redis baglanir
  - APScheduler baslatilir
Uygulama kapanirken hepsi duzgun sekilde kapatilir.

Router'lar ve CORS bu dosyada yapilandirilir.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import mongo
from core.redis_client import redis_manager
from routers.analysis import router as analysis_router
from routers.auth import router as auth_router
from tasks.scheduler import scheduler, configure_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
#  CORS IZINLI ORIGINLER
# ═══════════════════════════════════════════════

ALLOWED_ORIGINS = [
    "http://localhost:3000",      # Next.js dev
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "https://football-better.vercel.app",  # Production (Vercel deploy)
]


# ═══════════════════════════════════════════════
#  LIFESPAN (STARTUP / SHUTDOWN)
# ═══════════════════════════════════════════════


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Uygulama yasam dongusunu yonetir (startup → shutdown)."""

    # ── Startup ──
    await mongo.connect()
    logger.info("MongoDB baglantisi kuruldu.")

    await redis_manager.connect()
    logger.info("Redis baglantisi kuruldu.")

    configure_scheduler()
    scheduler.start()
    logger.info("Scheduler baslatildi.")

    yield

    # ── Shutdown ──
    scheduler.shutdown(wait=False)
    logger.info("Scheduler durduruldu.")

    await redis_manager.close()
    logger.info("Redis baglantisi kapatildi.")

    await mongo.close()
    logger.info("MongoDB baglantisi kapatildi.")


# ═══════════════════════════════════════════════
#  FASTAPI UYGULAMA NESNESI
# ═══════════════════════════════════════════════


app = FastAPI(
    title="Football SaaS API",
    description="Canli oran analiz sistemi backend servisi.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'lari bagla
app.include_router(auth_router)
app.include_router(analysis_router)


@app.get("/health")
async def health_check():
    """Sistem saglik kontrolu."""
    return {"status": "ok"}

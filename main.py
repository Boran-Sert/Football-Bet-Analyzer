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

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import mongo
from core.redis_client import redis_manager
from middleware.telemetry import TelemetryMiddleware
from routers.admin import router as admin_router
from routers.analysis import router as analysis_router
from routers.auth import router as auth_router
from routers.matches import router as matches_router
from tasks.scheduler import scheduler, configure_scheduler
from utils.exceptions import AppException, app_exception_handler, global_exception_handler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


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
    version="0.2.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Telemetry middleware
app.add_middleware(TelemetryMiddleware)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# ── Router'lar ──
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(matches_router)
app.include_router(analysis_router)


@app.get("/health")
async def health_check():
    """Sistem saglik kontrolu — MongoDB + Redis + Scheduler durumu."""
    health = {"status": "ok", "components": {}}

    # MongoDB ping
    try:
        db = mongo.get_db()
        await db.command("ping")
        health["components"]["mongodb"] = "healthy"
    except Exception:
        health["components"]["mongodb"] = "unhealthy"
        health["status"] = "degraded"

    # Redis ping
    try:
        redis = redis_manager.get_client()
        await redis.ping()
        health["components"]["redis"] = "healthy"
    except Exception:
        health["components"]["redis"] = "unhealthy"
        health["status"] = "degraded"

    # Scheduler
    health["components"]["scheduler"] = "running" if scheduler.running else "stopped"

    return health

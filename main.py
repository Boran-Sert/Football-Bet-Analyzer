"""FastAPI uygulama giris noktasi — billing router eklendi (GAP 4)."""

from fastapi import HTTPException
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import mongo
from core.redis_client import redis_manager
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from middleware.security import SecurityHeadersMiddleware
from middleware.telemetry import TelemetryMiddleware
from routers.admin import router as admin_router
from routers.analysis import router as analysis_router
from routers.auth import router as auth_router
from routers.billing import router as billing_router  # ← GAP 4: Stripe
from routers.matches import router as matches_router
from tasks.scheduler import scheduler, configure_scheduler
from fastapi.exceptions import RequestValidationError
from prometheus_fastapi_instrumentator import Instrumentator
from utils.exceptions import (
    AppException,
    app_exception_handler,
    global_exception_handler,
    validation_exception_handler,
)

from core.logger import logger

# setup_logging() is already called on import in core.logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    await mongo.connect()
    logger.info("MongoDB baglantisi kuruldu.")
    await redis_manager.connect()
    logger.info("Redis baglantisi kuruldu.")
    configure_scheduler()
    scheduler.start()
    logger.info("Scheduler baslatildi.")

    yield

    scheduler.shutdown(wait=False)
    logger.info("Scheduler durduruldu.")
    await redis_manager.close()
    logger.info("Redis baglantisi kapatildi.")
    await mongo.close()
    logger.info("MongoDB baglantisi kapatildi.")


app = FastAPI(
    title="Football SaaS API",
    description="Canli oran analiz sistemi backend servisi.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.TRUSTED_PROXIES)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(TelemetryMiddleware)

# CORSMiddleware EN SON eklenecek (En dışta çalışacak ve ilk OPTIONS'ı yakalayacak)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(matches_router)
app.include_router(analysis_router)
app.include_router(billing_router)

# Prometheus Metrikleri (Faz 3)
Instrumentator().instrument(app).expose(
    app, include_in_schema=False, tags=["Monitoring"]
)


from fastapi.responses import JSONResponse, Response


@app.get("/metrics")
async def metrics_endpoint(request: Request):
    """Custom metrics endpoint with IP whitelist."""
    client_ip = request.client.host if request.client else "unknown"
    allowed_ips = ["127.0.0.1", "::1"] + settings.TRUSTED_PROXIES

    if client_ip not in allowed_ips:
        logger.warning(f"Unauthorized metrics access attempt from {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden")

    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    health = {"status": "ok", "components": {}}

    try:
        db = mongo.get_db()
        await db.command("ping")
        health["components"]["mongodb"] = "healthy"
    except Exception:
        health["components"]["mongodb"] = "unhealthy"
        health["status"] = "degraded"

    try:
        redis = redis_manager.get_client()
        await redis.ping()
        health["components"]["redis"] = "healthy"
    except Exception:
        health["components"]["redis"] = "unhealthy"
        health["status"] = "degraded"

    health["components"]["scheduler"] = "running" if scheduler.running else "stopped"

    if health["status"] == "degraded":
        return JSONResponse(content=health, status_code=503)

    return health

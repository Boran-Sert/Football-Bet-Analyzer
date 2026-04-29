"""Ozel hata (exception) siniflari ve handler'lar."""

from fastapi import Request
from fastapi.responses import JSONResponse
from core.config import settings


class AppException(Exception):
    """Uygulama bazli ozel hata sinifi."""
    def __init__(self, status_code: int, detail: str, error_code: str = "INTERNAL_ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code


async def app_exception_handler(request: Request, exc: AppException):
    """AppException firlatildiginda temiz JSON doner."""
    origin = request.headers.get("origin")
    headers = {}
    if origin in settings.ALLOWED_ORIGINS or "*" in settings.ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin or "*"
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "detail": exc.detail},
        headers=headers
    )


async def global_exception_handler(request: Request, exc: Exception):
    """Unhandled tum hatalari yakalar, detayli traceback gizler."""
    import logging
    logging.getLogger(__name__).error("Unhandled exception: %s", exc, exc_info=True)
    
    origin = request.headers.get("origin")
    headers = {}
    if origin in settings.ALLOWED_ORIGINS or "*" in settings.ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin or "*"
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_SERVER_ERROR", "detail": "An unexpected error occurred."},
        headers=headers
    )

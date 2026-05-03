"""Standardized exception classes and handlers for global error management (Faz 3)."""

from fastapi import Request
from starlette.background import BackgroundTask
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from core.config import settings
from core.logger import logger

class AppException(Exception):
    """Custom application exception."""
    def __init__(self, status_code: int, message: str, detail: any = None, error_code: str = "BUSINESS_LOGIC_ERROR"):
        self.status_code = status_code
        self.message = message
        self.detail = detail
        self.error_code = error_code

def get_cors_headers(request: Request):
    """Helper to get CORS headers for error responses."""
    origin = request.headers.get("origin")
    headers = {}
    if origin in settings.ALLOWED_ORIGINS:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    return headers

async def app_exception_handler(request: Request, exc: AppException):
    """Handles AppException by returning a standardized JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "detail": exc.detail
        },
        headers=get_cors_headers(request)
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handles Pydantic validation errors."""
    return JSONResponse(
        status_code=422,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Input validation failed.",
            "detail": exc.errors()
        },
        headers=get_cors_headers(request)
    )

import httpx
import traceback

async def send_telegram_alert(message: str):
    """Sends a notification to Telegram if configured."""
    if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
        return
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": settings.TELEGRAM_CHAT_ID,
        "text": f"🚨 *CRITICAL ERROR* 🚨\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json=payload)
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {str(e)}")

async def global_exception_handler(request: Request, exc: Exception):
    """Catches all unhandled exceptions, logs to stdout (Loki), and alerts via Telegram."""
    error_msg = str(exc)
    stack_trace = traceback.format_exc()
    
    # Structure the log for Loki
    logger.error(
        f"Unhandled exception on {request.url.path}: {error_msg}",
        extra={
            "extra_fields": {
                "url": str(request.url),
                "method": request.method,
                "error": error_msg,
                "traceback": stack_trace
            }
        },
        exc_info=True
    )
    
    # Send Telegram alert for production critical errors
    if settings.ENVIRONMENT == "production":
        alert_text = (
            f"*Endpoint:* {request.method} {request.url.path}\n"
            f"*Error:* {error_msg}\n"
            f"*Traceback:* ```{stack_trace[:300]}...```" # Truncate to avoid limit
        )
        # Faz 6 Fix: Telegram alert'i BackgroundTask ile yolla (Self-DDoS engellendi)
        background = BackgroundTask(send_telegram_alert, alert_text)
    else:
        background = None
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred. Our team has been notified via Telegram.",
            "detail": None
        },
        headers=get_cors_headers(request),
        background=background
    )

"""Telemetri middleware'i.

Gelen istekleri yakalayip surelerini olcer.
BackgroundTasks kullanarak asenkron bir sekilde MongoDB'ye loglar.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from schemas.analytics import RequestLog
from core.logger import logger


class TelemetryMiddleware(BaseHTTPMiddleware):
    """Her istegi loglayan middleware."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Istegi isler, sureyi olcer ve arka planda log kaydini baslatir."""
        start_time = time.time()
        
        # Endpoint ve metoda ulas
        method = request.method
        endpoint = request.url.path

        # /health veya /docs gibi loglanmamasi gereken endpointler
        skip_endpoints = ["/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"]
        if any(endpoint.startswith(path) for path in skip_endpoints):
            return await call_next(request)

        # Istegi devam ettir ve yaniti bekle
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            # Ulasilamayan exception handlers tarafindan islenecek ama 
            # biz burada sureyi yakaliyoruz
            status_code = 500
            raise exc
        finally:
            process_time_ms = (time.time() - start_time) * 1000.0

            # Gecerli IP ve User Agent
            ip_address = request.client.host if request.client else ""
            user_agent = request.headers.get("user-agent", "")

            # Kullanici bilgisini al
            user_id = getattr(request.state, "user_id", None)

            # Log verisini hazirla
            log_data = RequestLog(
                user_id=str(user_id) if user_id else None,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                process_time_ms=process_time_ms,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # JSON formatinda stdout'a logla (Faz 2: Centralized Logging)
            logger.info(
                f"API Request: {method} {endpoint} {status_code}",
                extra={"extra_fields": log_data.model_dump()}
            )
        
        return response

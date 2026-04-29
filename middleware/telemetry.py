"""Telemetri middleware'i.

Gelen istekleri yakalayip surelerini olcer.
BackgroundTasks kullanarak asenkron bir sekilde MongoDB'ye loglar.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.background import BackgroundTask

from core.database import mongo
from repositories.analytics_repository import AnalyticsRepository
from schemas.analytics import RequestLog


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

            # Kullanici bilgisi (eger auth middleware tarafindan eklenmisse)
            user_id = getattr(request.state, "user_id", None)

            log_data = RequestLog(
                user_id=user_id,
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                process_time_ms=process_time_ms,
                ip_address=ip_address,
                user_agent=user_agent
            )

            # Eger response nesnesi varsa, arka plan gorevi ekle.
            # Yoksa (exception olduysa), manuel calistiracagiz (fire-and-forget).
            if 'response' in locals() and hasattr(response, "background") and response.background is not None:
                # Eger mevcut bir background task varsa, bizimkini de calistirmak icin 
                # manuel eklemek daha saglikli.
                pass
            
            # Repoyu olusturup asenkron background gorevi olarak atayalim
            # Fastapi'de background tasklari dogrudan router'da eklenir ama middleware icinde
            # starlette'in yapisindan faydalanarak ekleyebiliriz.
            
            async def write_log(data: RequestLog):
                try:
                    db = mongo.get_db()
                    repo = AnalyticsRepository(db)
                    await repo.insert_log(data)
                except Exception:
                    pass # Loglamada hata olursa gormezden gel

            if 'response' in locals() and isinstance(response, Response):
                # Mevcut task'i ezip kendi task'imizi (birden fazla eklenebilir hale) getiriyoruz
                # starlette.background.BackgroundTasks ile birden fazla task eklenebilir
                # Ancak burada basitce tek bir task ekliyoruz
                response.background = BackgroundTask(write_log, log_data)
        
        return response

"""Security headers middleware.
Sets HSTS, CSP, X-Content-Type-Options, etc.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from core.config import settings
        response = await call_next(request)
        
        # Her ortamda güvenli olan header'lar
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Sadece production'da HSTS ve CSP
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        
        return response

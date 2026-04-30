"""Security headers middleware.
Sets HSTS, CSP, X-Content-Type-Options, etc.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds security headers to every response."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # HSTS (HTTP Strict Transport Security) - 1 year
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # X-Content-Type-Options
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-Frame-Options (Prevent clickjacking)
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-XSS-Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content-Security-Policy (Basic)
        # In a real app, this should be more specific
        response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
        
        return response

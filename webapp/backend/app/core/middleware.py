"""
FastAPI middleware for rate limiting, request logging, and security headers.
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import time
from app.core.redis import RateLimiter, get_redis
from app.config import get_settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.

    Headers added:
    - X-Content-Type-Options: Prevent MIME type sniffing
    - X-Frame-Options: Prevent clickjacking
    - X-XSS-Protection: Enable XSS filter (legacy browsers)
    - Referrer-Policy: Control referrer information
    - Permissions-Policy: Restrict browser features
    - Strict-Transport-Security: Force HTTPS (production only)
    - Content-Security-Policy: Restrict resource loading
    """

    def __init__(self, app, enable_hsts: bool = False):
        super().__init__(app)
        self.enable_hsts = enable_hsts

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking - deny embedding in iframes
        response.headers["X-Frame-Options"] = "DENY"

        # XSS protection for legacy browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features
        response.headers["Permissions-Policy"] = (
            "accelerometer=(), camera=(), geolocation=(), "
            "gyroscope=(), magnetometer=(), microphone=(), "
            "payment=(), usb=()"
        )

        # HSTS - only in production (requires HTTPS)
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Basic CSP - adjust based on your frontend needs
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-ancestors 'none';"
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.

    Limits:
    - Anonymous: 30 requests per minute
    - Authenticated: 100 requests per minute
    - Strict endpoints (auth, payments): 10 requests per minute
    """

    # Endpoints with stricter limits
    STRICT_ENDPOINTS = ["/api/auth/login", "/api/auth/register", "/api/payments/"]

    def __init__(self, app, default_limit: int = 100, window: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting if Redis not available
        if not get_redis():
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"

        # Check for auth token to identify user
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token hash as identifier for authenticated users
            identifier = f"user:{hash(auth_header)}"
            limit = self.default_limit
        else:
            identifier = f"ip:{client_ip}"
            limit = 30  # Lower limit for anonymous

        # Stricter limit for sensitive endpoints
        path = request.url.path
        if any(path.startswith(ep) for ep in self.STRICT_ENDPOINTS):
            limit = 10
            identifier = f"strict:{identifier}"

        # Check rate limit
        if not RateLimiter.is_allowed(identifier, limit, self.window):
            remaining = RateLimiter.get_remaining(identifier, limit)
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": self.window
                },
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "Retry-After": str(self.window)
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = RateLimiter.get_remaining(identifier, limit)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request timing and errors."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log slow requests (> 5 seconds)
            if process_time > 5:
                print(f"[SLOW] {request.method} {request.url.path} - {process_time:.2f}s")

            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            return response

        except Exception as e:
            process_time = time.time() - start_time
            print(f"[ERROR] {request.method} {request.url.path} - {str(e)} ({process_time:.2f}s)")
            raise

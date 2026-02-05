"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, validate_settings
from app.database import init_db
from app.api import api_router
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.core.redis import get_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    # Startup
    print("Validating configuration...")
    validate_settings(settings)
    print("Configuration validated.")

    print("Initializing database...")
    init_db()
    print("Database initialized.")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="API for generating comprehensive research dossiers on companies and people.",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# CORS middleware - allow localhost on any port for development
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
if settings.frontend_url not in allowed_origins:
    allowed_origins.append(settings.frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not settings.debug else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting middleware (only in production or if Redis available)
if not settings.debug or get_redis():
    app.add_middleware(RateLimitMiddleware, default_limit=100, window=60)
    app.add_middleware(RequestLoggingMiddleware)

# Security headers middleware (always enabled, HSTS only in production)
app.add_middleware(SecurityHeadersMiddleware, enable_hsts=not settings.debug)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.api_version,
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    redis_status = "connected" if get_redis() else "not connected"
    return {
        "status": "healthy",
        "database": "connected",
        "redis": redis_status,
        "stripe": "configured" if settings.stripe_secret_key else "not configured",
        "email": "configured" if settings.resend_api_key else "not configured",
        "openai": "configured" if settings.openai_api_key else "not configured"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handle uncaught exceptions."""
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "type": type(exc).__name__}
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

"""API routes."""

from fastapi import APIRouter
from app.api import auth, research, payments, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(research.router, prefix="/research", tags=["Research"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])

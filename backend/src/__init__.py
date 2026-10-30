"""
Регистрация FastAPI роутеров из всех модулей.
"""

from fastapi import APIRouter

from .companies.api.v1 import router as companies_router

router = APIRouter(prefix="/api/v1")

router.include_router(companies_router)


__all__ = ["router"]

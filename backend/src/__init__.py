"""
Регистрация FastAPI роутеров из всех модулей.
"""

from fastapi import APIRouter

from .companies.api.v1 import router as companies_router
from .jobs.api.v1 import router as jobs_router
from .llm.api.v1 import router as llm_router
from .sites.api.v1 import preview_router
from .sites.api.v1 import router as sites_router

router = APIRouter(prefix="/api/v1")

router.include_router(companies_router)
router.include_router(jobs_router)
router.include_router(llm_router)
router.include_router(sites_router)


__all__ = ["preview_router", "router"]

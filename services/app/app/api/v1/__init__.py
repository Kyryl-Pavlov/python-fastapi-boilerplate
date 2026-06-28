from fastapi import APIRouter

from .auth import router as auth_router
from .cache_test import router as cache_router
from .events import router as events_router
from .health import router as health_router
from .media import router as media_router

router = APIRouter()
router.include_router(health_router)
router.include_router(auth_router, prefix="/auth")
router.include_router(media_router, prefix="/media")
router.include_router(events_router, prefix="/events")
router.include_router(cache_router)

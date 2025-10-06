from fastapi import APIRouter
from .endpoints import health
from .endpoints import auth

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])

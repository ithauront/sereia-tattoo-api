from fastapi import APIRouter
from .v1 import health
from .v1 import auth

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])

from fastapi import APIRouter

from app.api.v1 import me, user, vip_clients, client_credit_entries
from .v1 import health
from .v1 import auth

router = APIRouter()

router.include_router(health.router, tags=["health"])
router.include_router(auth.router, tags=["auth"])
router.include_router(user.router, tags=["users"])
router.include_router(me.router, tags=["me"])
router.include_router(vip_clients.router, tags=["vip-clients"])
router.include_router(client_credit_entries.router, tags=["client-credit-entries"])

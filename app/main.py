from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router as api_router
from app.application.event_bus.setup import setup_event_bus
from app.core.security import jwt_service
from app.infrastructure.email.brevo_email_service import BrevoEmailService


@asynccontextmanager
async def lifespan(app: FastAPI):
    email_service = BrevoEmailService()
    token_service = jwt_service

    transactional_bus, integration_bus = setup_event_bus(
        email_service=email_service, token_service=token_service
    )

    app.state.transactional_bus = transactional_bus
    app.state.integration_bus = integration_bus

    yield


app = FastAPI(title="sereia-tattoo-api", lifespan=lifespan)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["root"])
def root():
    return {"status": "ok", "docs": "/docs"}


app.include_router(api_router)

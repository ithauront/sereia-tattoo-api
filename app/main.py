from fastapi import FastAPI
from app.core.config import settings
from app.api import router as api_router

app = FastAPI(title="sereia-tattoo-api")


@app.get("/", tags=["root"])
def root():
    return {"status": "ok", "docs": "/docs"}


app.include_router(api_router, prefix=settings.API)

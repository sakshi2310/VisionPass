"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models as _models  # noqa: F401
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.schema import prepare_postgres_schema
from app.db.session import SessionLocal, engine
from app.services.bootstrap_service import seed_default_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hooks."""
    prepare_postgres_schema(engine)
    db = SessionLocal()
    try:
        seed_default_admin(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}

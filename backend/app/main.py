"""FastAPI application entrypoint."""

import asyncio
import contextlib
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models as _models  # noqa: F401
from app.api.v1.api import api_router
from app.core.config import settings
from app.db.schema import prepare_postgres_schema
from app.db.session import SessionLocal, engine
from app.models.camera import Camera
from app.services.bootstrap_service import seed_default_admin
from app.services.camera_frame_service import process_camera_frame
from app.services.camera_service import CameraError

logger = logging.getLogger(__name__)


def _poll_active_attendance_cameras_once() -> None:
    db = SessionLocal()
    try:
        cameras = (
            db.query(Camera)
            .filter(
                Camera.is_active.is_(True),
                Camera.assigned_feature_scope.in_(("attendance", "both")),
                Camera.snapshot_url.is_not(None),
            )
            .all()
        )
        for camera in cameras:
            try:
                process_camera_frame(
                    db,
                    camera.tenant_id,
                    camera.id,
                    recognize=True,
                    mark=True,
                )
            except CameraError as exc:
                logger.info(
                    "[LIVE_RECOGNITION] skipped tenant_id=%s camera_id=%s code=%s message=%s",
                    camera.tenant_id,
                    camera.id,
                    exc.code,
                    exc.message,
                )
            except Exception:
                logger.exception(
                    "[LIVE_RECOGNITION] background poll failed tenant_id=%s camera_id=%s",
                    camera.tenant_id,
                    camera.id,
                )
    finally:
        db.close()


async def _live_attendance_loop() -> None:
    interval_seconds = max(settings.camera_frame_interval_seconds, 5)
    logger.info("[LIVE_RECOGNITION] background worker started interval_seconds=%s", interval_seconds)
    while True:
        await asyncio.to_thread(_poll_active_attendance_cameras_once)
        await asyncio.sleep(interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan hooks."""

    prepare_postgres_schema(engine)
    db = SessionLocal()
    live_task: asyncio.Task | None = None
    try:
        if settings.seed_demo_data:
            seed_default_admin(
                db,
                include_operational_data=settings.environment.lower() != "test",
            )
        if settings.environment.lower() != "test":
            live_task = asyncio.create_task(_live_attendance_loop())
    finally:
        db.close()
    yield
    if live_task is not None:
        live_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await live_task


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

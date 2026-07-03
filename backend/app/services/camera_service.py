"""Tenant-scoped camera management and snapshot validation."""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt_credential, encrypt_credential
from app.models.camera import Camera
from app.services.alert_service import create_alert


class CameraError(ValueError):
    def __init__(self, code: str, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _queue_camera_alert(
    db: Session,
    camera: Camera,
    alert_type: str,
    message: str,
    code: str,
) -> None:
    tenant_id = getattr(camera, "tenant_id", None)
    if tenant_id is None:
        return
    create_alert(
        db,
        tenant_id=tenant_id,
        alert_type=alert_type,
        message=message,
        source_type="camera",
        source_id=camera.id,
        metadata={"camera_id": camera.id, "error_code": code},
    )


def _clean(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None


def _validate_configuration(
    camera_type: str,
    stream_url: str | None,
    snapshot_url: str | None,
) -> None:
    if camera_type == "ip_webcam" and not snapshot_url:
        raise CameraError("SNAPSHOT_URL_REQUIRED", "IP Webcam cameras require a snapshot URL.")
    if camera_type == "rtsp" and not stream_url:
        raise CameraError("STREAM_URL_REQUIRED", "RTSP cameras require a stream URL.")
    if snapshot_url and urlparse(snapshot_url).scheme.lower() not in {"http", "https"}:
        raise CameraError("INVALID_SNAPSHOT_URL", "Snapshot URL must use HTTP or HTTPS.")
    if camera_type == "rtsp" and stream_url and urlparse(stream_url).scheme.lower() not in {"rtsp", "rtsps"}:
        raise CameraError("INVALID_STREAM_URL", "RTSP stream URL must use RTSP or RTSPS.")


def camera_to_dict(camera: Camera) -> dict:
    return {
        "id": camera.id,
        "tenant_id": camera.tenant_id,
        "name": camera.name,
        "location": camera.location,
        "camera_type": camera.camera_type,
        "stream_url": camera.stream_url,
        "snapshot_url": camera.snapshot_url,
        "username": camera.username,
        "has_credentials": bool(camera.username or camera.password_encrypted),
        "is_active": camera.is_active,
        "health_status": camera.health_status,
        "last_seen_at": camera.last_seen_at,
        "created_at": camera.created_at,
        "updated_at": camera.updated_at,
    }


def list_cameras(db: Session, tenant_id: str) -> list[Camera]:
    return (
        db.query(Camera)
        .filter(Camera.tenant_id == tenant_id)
        .order_by(Camera.created_at.desc())
        .all()
    )


def get_camera(db: Session, tenant_id: str, camera_id: str) -> Camera | None:
    return (
        db.query(Camera)
        .filter(Camera.tenant_id == tenant_id, Camera.id == camera_id)
        .one_or_none()
    )


def create_camera(
    db: Session,
    tenant_id: str,
    *,
    name: str,
    location: str,
    camera_type: str,
    stream_url: str | None,
    snapshot_url: str | None,
    username: str | None,
    password: str | None,
    is_active: bool,
) -> Camera:
    normalized_name = name.strip()
    normalized_location = location.strip()
    if not normalized_name or not normalized_location:
        raise CameraError("INVALID_CAMERA", "Camera name and location are required.")
    stream_url = _clean(stream_url)
    snapshot_url = _clean(snapshot_url)
    _validate_configuration(camera_type, stream_url, snapshot_url)
    camera = Camera(
        tenant_id=tenant_id,
        name=normalized_name,
        location=normalized_location,
        camera_type=camera_type,
        stream_url=stream_url,
        snapshot_url=snapshot_url,
        username=_clean(username),
        password_encrypted=encrypt_credential(password) if password else None,
        is_active=is_active,
        health_status="unknown",
    )
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def update_camera(db: Session, tenant_id: str, camera_id: str, changes: dict) -> Camera | None:
    camera = get_camera(db, tenant_id, camera_id)
    if camera is None:
        return None
    if changes.get("camera_type") is None and "camera_type" in changes:
        raise CameraError("INVALID_CAMERA", "Camera type cannot be empty.")
    if changes.get("is_active") is None and "is_active" in changes:
        raise CameraError("INVALID_CAMERA", "Active status cannot be empty.")
    camera_type = changes.get("camera_type", camera.camera_type)
    stream_url = _clean(changes["stream_url"]) if "stream_url" in changes else camera.stream_url
    snapshot_url = _clean(changes["snapshot_url"]) if "snapshot_url" in changes else camera.snapshot_url
    _validate_configuration(camera_type, stream_url, snapshot_url)
    for required_field in ("name", "location"):
        if required_field in changes:
            value = changes[required_field]
            if not isinstance(value, str) or not value.strip():
                raise CameraError("INVALID_CAMERA", "Camera name and location are required.")

    for field in ("name", "location", "camera_type", "username", "is_active"):
        if field in changes:
            value = changes[field]
            if field == "username":
                value = _clean(value)
            elif isinstance(value, str):
                value = value.strip()
            setattr(camera, field, value)
    camera.stream_url = stream_url
    camera.snapshot_url = snapshot_url
    if changes.get("clear_password"):
        camera.password_encrypted = None
    elif changes.get("password"):
        camera.password_encrypted = encrypt_credential(changes["password"])
    camera.health_status = "unknown"
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return camera


def delete_camera(db: Session, tenant_id: str, camera_id: str) -> bool:
    camera = get_camera(db, tenant_id, camera_id)
    if camera is None:
        return False
    db.delete(camera)
    db.commit()
    return True


def fetch_snapshot(db: Session, camera: Camera) -> dict:
    if not camera.snapshot_url:
        camera.health_status = "error"
        _queue_camera_alert(
            db,
            camera,
            "CAMERA_ERROR",
            "Camera health check failed because no snapshot URL is configured.",
            "SNAPSHOT_URL_REQUIRED",
        )
        db.add(camera)
        db.commit()
        raise CameraError("SNAPSHOT_URL_REQUIRED", "This camera does not have a snapshot URL.", status_code=422)

    auth = None
    password = decrypt_credential(camera.password_encrypted)
    if camera.username:
        auth = httpx.BasicAuth(camera.username, password or "")
    try:
        with httpx.Client(
            timeout=settings.camera_request_timeout_seconds,
            follow_redirects=True,
        ) as client:
            response = client.get(camera.snapshot_url, auth=auth)
            response.raise_for_status()
            content = response.content
        if len(content) > settings.upload_max_image_mb * 1024 * 1024:
            raise CameraError("SNAPSHOT_TOO_LARGE", "Camera snapshot exceeds the image size limit.", status_code=502)

        import cv2
        import numpy as np

        image = cv2.imdecode(np.frombuffer(content, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None or image.size == 0:
            raise CameraError("INVALID_SNAPSHOT", "Camera response is not a readable image.", status_code=502)
        height, width = image.shape[:2]
        content_type = response.headers.get("content-type", "image/jpeg").split(";", 1)[0]
        if not content_type.startswith("image/"):
            content_type = "image/jpeg"
    except CameraError as exc:
        camera.health_status = "error"
        _queue_camera_alert(db, camera, "CAMERA_ERROR", exc.message, exc.code)
        db.add(camera)
        db.commit()
        raise
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        camera.health_status = "offline"
        _queue_camera_alert(
            db,
            camera,
            "CAMERA_OFFLINE",
            "Camera could not be reached during its health check.",
            "CAMERA_OFFLINE",
        )
        db.add(camera)
        db.commit()
        raise CameraError("CAMERA_OFFLINE", "Camera could not be reached.", status_code=502) from exc
    except httpx.HTTPError as exc:
        camera.health_status = "error"
        _queue_camera_alert(
            db,
            camera,
            "CAMERA_ERROR",
            "Camera returned an unsuccessful response during its health check.",
            "CAMERA_REQUEST_FAILED",
        )
        db.add(camera)
        db.commit()
        raise CameraError("CAMERA_REQUEST_FAILED", "Camera returned an unsuccessful response.", status_code=502) from exc

    camera.health_status = "online"
    camera.last_seen_at = datetime.now(timezone.utc)
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return {
        "content": content,
        "content_type": content_type,
        "width": width,
        "height": height,
    }

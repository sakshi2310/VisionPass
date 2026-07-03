"""Camera snapshot processing, recognition, and attendance orchestration."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.camera import CameraEvent
from app.services.attendance_service import (
    AttendanceMarkError,
    determine_next_attendance_event,
    mark_attendance,
)
from app.services.camera_service import CameraError, fetch_snapshot, get_camera
from app.services.face_ai_service import FaceModelUnavailableError, FaceValidationError
from app.services.recognition_service import recognize_employee_face


def log_camera_event(
    db: Session,
    *,
    tenant_id: str,
    camera_id: str,
    event_type: str,
    recognition_status: str,
    employee_id: str | None = None,
    confidence: float | None = None,
    image_path: str | None = None,
    metadata: dict | None = None,
) -> CameraEvent:
    event = CameraEvent(
        tenant_id=tenant_id,
        camera_id=camera_id,
        event_type=event_type,
        employee_id=employee_id,
        recognition_status=recognition_status,
        confidence=confidence,
        image_path=image_path,
        event_metadata=metadata or {},
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def process_camera_frame(
    db: Session,
    tenant_id: str,
    camera_id: str,
    *,
    recognize: bool,
    mark: bool = False,
) -> dict:
    """Fetch and validate a frame, optionally recognize and mark attendance."""

    camera = get_camera(db, tenant_id, camera_id)
    if camera is None:
        raise CameraError("CAMERA_NOT_FOUND", "Camera not found.", status_code=404)
    if not camera.is_active:
        raise CameraError("CAMERA_INACTIVE", "Camera is inactive.", status_code=409)

    event_type = "attendance_recognition" if mark else "face_recognition" if recognize else "frame_processed"
    try:
        snapshot = fetch_snapshot(db, camera)
    except CameraError as exc:
        log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status=exc.code,
            metadata={"error": exc.message},
        )
        raise

    frame_metadata = {
        "width": snapshot["width"],
        "height": snapshot["height"],
        "content_type": snapshot["content_type"],
        "frame_interval_seconds": settings.camera_frame_interval_seconds,
        "request_timeout_seconds": settings.camera_request_timeout_seconds,
    }
    if not recognize:
        camera_event = log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status="FRAME_CAPTURED",
            metadata=frame_metadata,
        )
        return {
            "camera": camera,
            "camera_event": camera_event,
            "frame": frame_metadata,
            "recognition": None,
            "attendance": None,
        }

    try:
        recognition = recognize_employee_face(db, tenant_id, snapshot["content"])
    except FaceValidationError as exc:
        log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status=exc.code,
            metadata={**frame_metadata, "error": exc.message},
        )
        raise
    except FaceModelUnavailableError:
        log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status="MODEL_UNAVAILABLE",
            metadata=frame_metadata,
        )
        raise
    attendance = None
    if mark and recognition["recognized"]:
        try:
            attendance_event_type = determine_next_attendance_event(
                db,
                tenant_id,
                recognition["employee_id"],
            )
            attendance = mark_attendance(
                db,
                tenant_id,
                recognition["employee_id"],
                event_type=attendance_event_type,
                source="camera",
                camera_id=camera.id,
                confidence=recognition["confidence"],
                metadata={
                    "recognition_status": recognition["recognition_status"],
                    "recognition_distance": recognition["distance"],
                },
            )
        except AttendanceMarkError as exc:
            log_camera_event(
                db,
                tenant_id=tenant_id,
                camera_id=camera.id,
                event_type=event_type,
                recognition_status=recognition["recognition_status"],
                employee_id=recognition["employee_id"],
                confidence=recognition["confidence"],
                metadata={**frame_metadata, "attendance_error": exc.code},
            )
            raise

    camera_event = log_camera_event(
        db,
        tenant_id=tenant_id,
        camera_id=camera.id,
        event_type=event_type,
        recognition_status=recognition["recognition_status"],
        employee_id=recognition["employee_id"],
        confidence=recognition["confidence"],
        metadata={
            **frame_metadata,
            "distance": recognition["distance"],
            "threshold": recognition["threshold"],
            "attendance_event_type": (
                attendance["event"].event_type if attendance is not None else None
            ),
        },
    )
    return {
        "camera": camera,
        "camera_event": camera_event,
        "frame": frame_metadata,
        "recognition": recognition,
        "attendance": attendance,
    }

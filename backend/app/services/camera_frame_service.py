"""Camera snapshot processing, recognition, and attendance orchestration."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.camera import CameraEvent
from app.services.attendance_service import (
    AttendanceMarkError,
    log_live_recognition_decision,
    process_camera_presence_recognition,
)
from app.services.camera_service import CameraError, fetch_snapshot, get_camera
from app.services.face_ai_service import FaceModelUnavailableError, FaceValidationError
from app.services.person_detection_service import create_person_detections
from app.services.recognition_service import recognize_employee_face

logger = logging.getLogger(__name__)


def _log_frame_decision(
    *,
    tenant_id: str,
    camera_id: str | None,
    camera_enabled: bool,
    frame_received: bool,
    face_detected: bool,
    matched: bool,
    employee_id: str | None,
    employee_name: str | None,
    confidence: float | None,
    decided_event: str,
    final_status: str,
    reason: str,
) -> None:
    log_live_recognition_decision(
        tenant_id=tenant_id,
        camera_id=camera_id,
        camera_enabled=camera_enabled,
        frame_received=frame_received,
        face_detected=face_detected,
        matched=matched,
        employee_id=employee_id,
        employee_name=employee_name,
        confidence=confidence,
        decided_event=decided_event,
        final_status=final_status,
        reason=reason,
    )


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
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera_id,
            camera_enabled=False,
            frame_received=False,
            face_detected=False,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=None,
            decided_event="error",
            final_status="error",
            reason="Camera not found",
        )
        raise CameraError("CAMERA_NOT_FOUND", "Camera not found.", status_code=404)
    if not camera.is_active:
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=False,
            frame_received=False,
            face_detected=False,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=None,
            decided_event="error",
            final_status="error",
            reason="Camera is inactive",
        )
        raise CameraError("CAMERA_INACTIVE", "Camera is inactive.", status_code=409)

    event_type = "attendance_recognition" if mark else "face_recognition" if recognize else "frame_processed"
    try:
        snapshot = fetch_snapshot(db, camera)
    except CameraError as exc:
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=bool(camera.is_active),
            frame_received=True,
            face_detected=False,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=None,
            decided_event="error",
            final_status="error",
            reason=exc.message,
        )
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
    person_detections = create_person_detections(
        db,
        tenant_id,
        camera.id,
        snapshot["content"],
        content_type=snapshot["content_type"],
    )
    if not recognize:
        camera_event = log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status="FRAME_CAPTURED",
            metadata={**frame_metadata, "person_detection_count": len(person_detections)},
        )
        return {
            "camera": camera,
            "camera_event": camera_event,
            "frame": frame_metadata,
            "recognition": None,
            "attendance": None,
            "person_detections": person_detections,
        }

    try:
        recognition = recognize_employee_face(db, tenant_id, snapshot["content"])
    except FaceValidationError as exc:
        metrics = getattr(exc, "metrics", {}) or {}
        face_detected = exc.code not in {"NO_FACE_DETECTED"}
        decided_event = "no_face" if exc.code == "NO_FACE_DETECTED" else "error"
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=bool(camera.is_active),
            frame_received=True,
            face_detected=face_detected,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=metrics.get("detection_confidence"),
            decided_event=decided_event,
            final_status="not_detected",
            reason=exc.message,
        )
        log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status=exc.code,
            metadata={**frame_metadata, "error": exc.message, "person_detection_count": len(person_detections)},
        )
        raise
    except FaceModelUnavailableError:
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=bool(camera.is_active),
            frame_received=True,
            face_detected=False,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=None,
            decided_event="error",
            final_status="error",
            reason="Face model unavailable",
        )
        log_camera_event(
            db,
            tenant_id=tenant_id,
            camera_id=camera.id,
            event_type=event_type,
            recognition_status="MODEL_UNAVAILABLE",
            metadata={**frame_metadata, "person_detection_count": len(person_detections)},
        )
        raise
    attendance = None
    attendance_decision = None
    attendance_reason = None
    if not recognition["recognized"]:
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=bool(camera.is_active),
            frame_received=True,
            face_detected=recognition["recognition_status"] != "NO_FACE",
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=recognition.get("confidence"),
            decided_event=(
                "no_face"
                if recognition["recognition_status"] == "NO_FACE"
                else "unknown_face"
                if recognition["recognition_status"] == "UNKNOWN"
                else "error"
            ),
            final_status="not_detected",
            reason=(
                "No face detected"
                if recognition["recognition_status"] == "NO_FACE"
                else "Unknown face detected"
                if recognition["recognition_status"] == "UNKNOWN"
                else "Face did not match"
            ),
        )
    if mark and recognition["recognized"]:
        try:
            presence = process_camera_presence_recognition(
                db,
                tenant_id,
                employee_id=recognition["employee_id"],
                employee_name=recognition.get("employee_name"),
                confidence=recognition["confidence"],
                recognition_status=recognition["recognition_status"],
                camera_id=camera.id,
                camera_enabled=camera.is_active,
            )
            attendance = presence["attendance"]
            attendance_decision = presence["decision"]
            attendance_reason = presence["reason"]
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
    elif recognition["recognized"]:
        _log_frame_decision(
            tenant_id=tenant_id,
            camera_id=camera.id,
            camera_enabled=bool(camera.is_active),
            frame_received=True,
            face_detected=True,
            matched=True,
            employee_id=recognition["employee_id"],
            employee_name=recognition.get("employee_name"),
            confidence=recognition["confidence"],
            decided_event="check_in",
            final_status="recognized",
            reason="Face matched; attendance event not requested.",
        )

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
            "attendance_event_type": attendance["event"].event_type if attendance is not None else None,
            "attendance_status": attendance["daily"].status if attendance is not None else None,
            "attendance_decision": attendance_decision,
            "attendance_reason": attendance_reason,
            "person_detection_count": len(person_detections),
            "person_detection_ids": [detection.id for detection in person_detections],
        },
    )
    return {
        "camera": camera,
        "camera_event": camera_event,
        "frame": frame_metadata,
        "recognition": recognition,
        "attendance": attendance,
        "person_detections": person_detections,
    }

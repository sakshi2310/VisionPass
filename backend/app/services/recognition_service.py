"""Tenant-scoped face recognition service."""

from __future__ import annotations

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.db.vector import Vector
from app.services.employee_service import get_or_create_face_settings
from app.services.alert_service import create_alert
from app.services.face_ai_service import (
    INVALID_IMAGE,
    LOW_FACE_CONFIDENCE,
    LOW_IMAGE_QUALITY,
    MULTIPLE_FACES_DETECTED,
    NO_FACE_DETECTED,
    FaceValidationError,
    analyze_face_image,
)


def find_best_employee_match(
    db: Session,
    tenant_id: str,
    embedding: list[float],
) -> dict | None:
    """Return the nearest active enrolled employee inside one tenant."""

    statement = text(
        """
        SELECT face.employee_id,
               employee.full_name AS employee_name,
               face.embedding <=> :embedding AS distance,
               1 - (face.embedding <=> :embedding) AS confidence
        FROM employee_face_embeddings AS face
        JOIN attendance_employees AS employee
          ON employee.id = face.employee_id
         AND employee.tenant_id = face.tenant_id
        WHERE face.tenant_id = :tenant_id
          AND face.is_active = TRUE
          AND employee.is_active = TRUE
        ORDER BY face.embedding <=> :embedding
        LIMIT 1
        """
    ).bindparams(bindparam("embedding", type_=Vector(512)))
    row = db.execute(
        statement,
        {"tenant_id": tenant_id, "embedding": embedding},
    ).mappings().first()
    if row is None:
        return None
    return {
        "employee_id": str(row["employee_id"]),
        "employee_name": row["employee_name"],
        "distance": float(row["distance"]),
        "confidence": float(row["confidence"]),
    }


def _unmatched(
    status: str,
    *,
    confidence: float | None = None,
    distance: float | None = None,
    face_count: int | None = None,
) -> dict:
    return {
        "recognized": False,
        "employee_id": None,
        "employee_name": None,
        "confidence": confidence,
        "distance": distance,
        "threshold": app_settings.face_recognition_threshold,
        "recognition_status": status,
        "face_count": face_count,
    }


def _queue_recognition_alert(db: Session, tenant_id: str, result: dict) -> None:
    status = result["recognition_status"]
    if status == "UNKNOWN":
        create_alert(
            db,
            tenant_id=tenant_id,
            alert_type="UNKNOWN_FACE",
            message="A face could not be matched to an active enrolled employee.",
            source_type="face_recognition",
            metadata={"recognition_status": status, "confidence": result.get("confidence")},
        )
    elif status == "LOW_CONFIDENCE":
        create_alert(
            db,
            tenant_id=tenant_id,
            alert_type="LOW_CONFIDENCE_FACE",
            message="A face match did not meet the configured confidence threshold.",
            source_type="face_recognition",
            metadata={
                "recognition_status": status,
                "confidence": result.get("confidence"),
                "threshold": result.get("threshold"),
            },
        )


def recognize_employee_face(
    db: Session,
    tenant_id: str,
    image_content: bytes,
) -> dict:
    """Analyze an image and match its face against this tenant only."""

    face_settings = get_or_create_face_settings(db, tenant_id)
    try:
        analysis = analyze_face_image(
            image_content,
            min_resolution_width=face_settings.min_resolution_width,
            min_resolution_height=face_settings.min_resolution_height,
            min_face_size_px=face_settings.min_face_size_px,
            min_sharpness_score=float(face_settings.max_blur_score),
            min_brightness=float(face_settings.min_brightness),
            max_brightness=float(face_settings.max_brightness),
        )
    except FaceValidationError as exc:
        if exc.code == NO_FACE_DETECTED:
            return _unmatched("NO_FACE", face_count=int(exc.metrics.get("face_count") or 0))
        if exc.code == MULTIPLE_FACES_DETECTED:
            return _unmatched("MULTIPLE_FACES", face_count=int(exc.metrics.get("face_count") or 2))
        if exc.code in {LOW_FACE_CONFIDENCE, LOW_IMAGE_QUALITY}:
            confidence = exc.metrics.get("detection_confidence")
            result = _unmatched(
                "LOW_CONFIDENCE",
                confidence=float(confidence) if confidence is not None else None,
                face_count=int(exc.metrics.get("face_count") or 1),
            )
            _queue_recognition_alert(db, tenant_id, result)
            return result
        if exc.code == INVALID_IMAGE:
            raise
        raise

    match = find_best_employee_match(db, tenant_id, analysis.embedding)
    if match is None:
        result = _unmatched("UNKNOWN", face_count=analysis.face_count)
        _queue_recognition_alert(db, tenant_id, result)
        return result

    confidence = match["confidence"]
    distance = match["distance"]
    if confidence < app_settings.face_recognition_threshold:
        result = _unmatched(
            "LOW_CONFIDENCE",
            confidence=confidence,
            distance=distance,
            face_count=analysis.face_count,
        )
        _queue_recognition_alert(db, tenant_id, result)
        return result

    return {
        "recognized": True,
        "employee_id": match["employee_id"],
        "employee_name": match["employee_name"],
        "confidence": confidence,
        "distance": distance,
        "threshold": app_settings.face_recognition_threshold,
        "recognition_status": "MATCHED",
        "face_count": analysis.face_count,
    }

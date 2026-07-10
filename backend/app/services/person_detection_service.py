"""Tenant-scoped person detection persistence and matching."""

from __future__ import annotations

import base64
from datetime import datetime, timedelta, timezone
import mimetypes
from pathlib import Path
from uuid import uuid4

import numpy as np
from sqlalchemy import String, cast, func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.employee import AttendanceEmployee, EmployeeFaceEmbedding, EmployeeFaceImage, EmployeeFaceProfile
from app.models.person_detection import PersonDetection
from app.models.visitor import Visitor
from app.services.feature_flag_service import list_enabled_modules
from app.services.employee_service import get_or_create_face_settings
from app.services.face_ai_service import FaceModelUnavailableError, FaceValidationError, detect_faces_in_image
from app.services.employee_service import create_employee
from app.services.recognition_service import find_best_employee_match
from app.services.visitor_service import VisitorError, create_visitor, record_visitor_visit

_IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
_ACTIVE_DETECTION_STATUSES = {"new", "reviewed", "suspicious", "converted_to_visitor", "converted_to_staff"}
_DETECTION_DEDUPE_WINDOW = timedelta(minutes=5)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/")


def _store_snapshot(
    *,
    tenant_id: str,
    camera_id: str,
    image_content: bytes,
    content_type: str | None,
    detected_at: datetime,
) -> str | None:
    if settings.storage_backend != "local":
        return None
    extension = _IMAGE_EXTENSIONS.get((content_type or "").lower(), ".jpg")
    timestamp = detected_at.astimezone(timezone.utc).strftime("%Y%m%d/%H%M%S")
    filename = f"{timestamp}-{uuid4().hex}{extension}"
    relative_path = Path(settings.upload_dir) / "person-detections" / tenant_id / camera_id / filename
    absolute_path = (Path.cwd() / relative_path).resolve()
    try:
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(image_content)
    except OSError:
        return None
    return _normalize_path(str(absolute_path))


def _load_image_bytes_from_path(path_value: str | None) -> bytes | None:
    if not path_value:
        return None
    raw_value = path_value.strip()
    if not raw_value:
        return None
    if raw_value.startswith("data:") and "," in raw_value:
        encoded = raw_value.split(",", 1)[1]
        try:
            return base64.b64decode(encoded)
        except Exception:
            return None
    if raw_value.startswith(("http://", "https://")):
        return None
    candidate = Path(raw_value)
    if candidate.is_file():
        try:
            return candidate.read_bytes()
        except OSError:
            return None
    return None


def _vector_distance(left: list[float], right: list[float]) -> float:
    left_vec = np.asarray(left, dtype=np.float32).reshape(-1)
    right_vec = np.asarray(right, dtype=np.float32).reshape(-1)
    if left_vec.size == 0 or right_vec.size == 0:
        return 1.0
    return float(1.0 - float(np.dot(left_vec, right_vec)))


def _detection_seen_at(detection: PersonDetection) -> datetime:
    return detection.last_seen_at or detection.detected_at


def _is_better_snapshot(current_quality: float | None, detection: PersonDetection) -> bool:
    if current_quality is None:
        return False
    if detection.snapshot_quality_score is None:
        return True
    return current_quality > float(detection.snapshot_quality_score)


def _image_data_url_from_path(path_value: str | None) -> str | None:
    image_bytes = _load_image_bytes_from_path(path_value)
    if image_bytes is None:
        return path_value
    media_type = mimetypes.guess_type(path_value or "")[0] or "image/jpeg"
    encoded = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{media_type};base64,{encoded}"


def _touch_detected_person(
    detection: PersonDetection,
    *,
    timestamp: datetime,
    snapshot_path: str | None,
    quality_score: float | None,
    face_embedding: list[float] | None,
    match_type: str,
    matched_staff_id: str | None,
    matched_visitor_id: str | None,
) -> None:
    if detection.first_seen_at is None:
        detection.first_seen_at = detection.detected_at or timestamp
    detection.last_seen_at = timestamp
    detection.seen_count = int(detection.seen_count or 0) + 1
    if detection.face_embedding is None and face_embedding is not None:
        detection.face_embedding = face_embedding
    if detection.match_type == "unknown" and match_type != "unknown":
        detection.match_type = match_type
        detection.matched_staff_id = matched_staff_id
        detection.matched_visitor_id = matched_visitor_id
    if snapshot_path and (_is_better_snapshot(quality_score, detection) or detection.image_path is None):
        detection.image_path = snapshot_path
        detection.snapshot_quality_score = quality_score


def _find_recent_duplicate_detection(
    db: Session,
    *,
    tenant_id: str,
    camera_id: str,
    timestamp: datetime,
    face_embedding: list[float] | None,
    match_type: str,
    matched_staff_id: str | None,
    matched_visitor_id: str | None,
    threshold: float,
) -> PersonDetection | None:
    cutoff = timestamp - _DETECTION_DEDUPE_WINDOW
    base_query = (
        db.query(PersonDetection)
        .filter(
            PersonDetection.tenant_id == tenant_id,
            PersonDetection.camera_id == camera_id,
            PersonDetection.status.in_(_ACTIVE_DETECTION_STATUSES),
            func.coalesce(PersonDetection.last_seen_at, PersonDetection.detected_at) >= cutoff,
        )
        .order_by(func.coalesce(PersonDetection.last_seen_at, PersonDetection.detected_at).desc(), PersonDetection.created_at.desc())
    )

    if match_type == "staff" and matched_staff_id is not None:
        existing = base_query.filter(PersonDetection.matched_staff_id == matched_staff_id).first()
        if existing is not None:
            return existing
    if match_type == "visitor" and matched_visitor_id is not None:
        existing = base_query.filter(PersonDetection.matched_visitor_id == matched_visitor_id).first()
        if existing is not None:
            return existing

    if face_embedding is None:
        return None

    embedding_query = base_query.filter(PersonDetection.face_embedding.isnot(None))
    if match_type in {"staff", "visitor"}:
        embedding_query = embedding_query.filter(PersonDetection.match_type == "unknown")

    best_match: PersonDetection | None = None
    best_distance = threshold
    for candidate in embedding_query.all():
        if candidate.face_embedding is None:
            continue
        distance = _vector_distance(candidate.face_embedding, face_embedding)
        if distance > threshold:
            continue
        if best_match is None or distance < best_distance or (
            distance == best_distance and _detection_seen_at(candidate) > _detection_seen_at(best_match)
        ):
            best_match = candidate
            best_distance = distance
    return best_match


def find_best_visitor_match(db: Session, tenant_id: str, embedding: list[float]) -> dict | None:
    visitors = (
        db.query(Visitor)
        .filter(
            Visitor.tenant_id == tenant_id,
            Visitor.photo_path.isnot(None),
            Visitor.status != "blocked",
        )
        .order_by(Visitor.updated_at.desc(), Visitor.created_at.desc())
        .all()
    )
    best_match: dict | None = None
    settings_row = get_or_create_face_settings(db, tenant_id)
    threshold = float(settings.face_recognition_threshold)
    for visitor in visitors:
        photo_bytes = _load_image_bytes_from_path(visitor.photo_path)
        if photo_bytes is None:
            continue
        try:
            faces = detect_faces_in_image(
                photo_bytes,
                min_resolution_width=settings_row.min_resolution_width,
                min_resolution_height=settings_row.min_resolution_height,
                min_face_size_px=settings_row.min_face_size_px,
                min_sharpness_score=float(settings_row.max_blur_score),
                min_brightness=float(settings_row.min_brightness),
                max_brightness=float(settings_row.max_brightness),
            )
        except (FaceModelUnavailableError, FaceValidationError):
            continue
        if not faces:
            continue
        distance = _vector_distance(faces[0].embedding, embedding)
        confidence = 1.0 - distance
        if confidence < threshold:
            continue
        if best_match is None or confidence > best_match["confidence"]:
            best_match = {
                "visitor_id": str(visitor.id),
                "visitor_name": visitor.full_name,
                "distance": distance,
                "confidence": confidence,
            }
    if best_match is None:
        return None
    return best_match


def _choose_match(
    *,
    staff_match: dict | None,
    visitor_match: dict | None,
) -> tuple[str, str | None, str | None]:
    if staff_match is not None and visitor_match is not None:
        if float(visitor_match["confidence"]) > float(staff_match["confidence"]):
            return "visitor", None, str(visitor_match["visitor_id"])
        return "staff", str(staff_match["employee_id"]), None
    if staff_match is not None:
        return "staff", str(staff_match["employee_id"]), None
    if visitor_match is not None:
        return "visitor", None, str(visitor_match["visitor_id"])
    return "unknown", None, None


def _set_detection_status(detection: PersonDetection, status: str) -> PersonDetection:
    detection.status = status
    return detection


def _prepare_visitor_payload(detection: PersonDetection, values: dict) -> dict:
    return {
        "name": values.get("name") or values.get("full_name") or "Unknown Visitor",
        "phone": values.get("phone"),
        "purpose": values.get("purpose"),
        "status": values.get("status") or "active",
        "notes": values.get("notes"),
        "image_path": detection.image_path,
        "face_embedding": detection.face_embedding,
    }


def _prepare_staff_email(values: dict) -> str:
    email = values.get("email")
    if isinstance(email, str) and email.strip():
        return email.strip().lower()
    return f"staff-{uuid4().hex[:12]}@visionpass.local"


def _update_employee_face_profile(
    db: Session,
    *,
    tenant_id: str,
    employee_id: str,
    quality_score: float | None,
    enrolled_at: datetime,
) -> EmployeeFaceProfile:
    profile = (
        db.query(EmployeeFaceProfile)
        .filter(EmployeeFaceProfile.tenant_id == tenant_id, EmployeeFaceProfile.employee_id == employee_id)
        .one_or_none()
    )
    if profile is None:
        profile = EmployeeFaceProfile(tenant_id=tenant_id, employee_id=employee_id)
        db.add(profile)
        db.flush()

    profile.face_count = db.query(EmployeeFaceImage.id).filter(
        EmployeeFaceImage.tenant_id == tenant_id,
        EmployeeFaceImage.employee_id == employee_id,
    ).count()
    profile.embedding_count = db.query(EmployeeFaceEmbedding.id).filter(
        EmployeeFaceEmbedding.tenant_id == tenant_id,
        EmployeeFaceEmbedding.employee_id == employee_id,
        EmployeeFaceEmbedding.is_active.is_(True),
    ).count()
    profile.average_quality_score = quality_score
    profile.last_enrolled_at = enrolled_at
    profile.enrollment_status = "Enrolled" if profile.embedding_count else "Failed"
    db.add(profile)
    return profile


def add_staff_from_person_detection(
    db: Session,
    tenant_id: str,
    detection_id: str,
    actor_id: str,
    values: dict,
) -> dict | None:
    try:
        detection = get_person_detection(db, tenant_id, detection_id)
        if detection is None:
            return None
        if detection.match_type != "unknown":
            raise VisitorError("Only unknown detections can be converted to staff", status_code=422)
        if detection.status == "converted_to_staff":
            raise VisitorError("Person detection already converted to staff", status_code=409)
        if detection.face_embedding is None:
            raise VisitorError("A matching face embedding is required to convert this detection to staff", status_code=422)

        employee = create_employee(
            db,
            tenant_id,
            employee_code=values.get("employee_code"),
            full_name=values["full_name"],
            email=_prepare_staff_email(values),
            mobile=values.get("mobile"),
            department=values.get("department"),
            designation=values.get("designation"),
            joining_date=values.get("joining_date"),
            is_active=(values.get("status", "active") == "active"),
            commit=False,
        )

        face_settings = get_or_create_face_settings(db, tenant_id)
        image_source = _image_data_url_from_path(detection.image_path)
        image = EmployeeFaceImage(
            tenant_id=tenant_id,
            employee_id=employee.id,
            image_url=image_source or detection.image_path or "",
            original_filename=f"person-detection-{detection.id}.jpg",
            image_type=mimetypes.guess_type(detection.image_path or "")[0] if detection.image_path else "image/jpeg",
            quality_score=detection.snapshot_quality_score,
            face_detected=True,
            face_count=1,
            validation_status="Validated",
            validation_message="Imported from person detection",
            embedding_generated=True,
        )
        db.add(image)
        db.flush()

        embedding = EmployeeFaceEmbedding(
            tenant_id=tenant_id,
            employee_id=employee.id,
            face_image_id=image.id,
            embedding=detection.face_embedding,
            embedding_model=face_settings.embedding_model,
            version=face_settings.embedding_version,
            quality_score=detection.snapshot_quality_score,
            is_active=True,
        )
        db.add(embedding)
        db.flush()

        profile = _update_employee_face_profile(
            db,
            tenant_id=tenant_id,
            employee_id=employee.id,
            quality_score=detection.snapshot_quality_score,
            enrolled_at=_detection_seen_at(detection),
        )

        detection.match_type = "staff"
        detection.matched_staff_id = employee.id
        detection.matched_visitor_id = None
        detection.status = "converted_to_staff"
        db.add_all([detection, employee, image, embedding, profile])
        db.commit()
        db.refresh(employee)
        db.refresh(image)
        db.refresh(embedding)
        db.refresh(profile)
        db.refresh(detection)
        return {
            "employee": employee,
            "face_profile": profile,
            "person_detection": detection,
        }
    except Exception:
        db.rollback()
        raise


def create_person_detections(
    db: Session,
    tenant_id: str,
    camera_id: str,
    image_content: bytes,
    *,
    content_type: str | None = None,
    detected_at: datetime | None = None,
    zone_id: str | None = None,
) -> list[PersonDetection]:
    if "visitor_unknown" not in list_enabled_modules(db, tenant_id):
        return []
    settings_row = get_or_create_face_settings(db, tenant_id)
    threshold = float(settings.face_recognition_threshold)
    try:
        faces = detect_faces_in_image(
            image_content,
            min_resolution_width=settings_row.min_resolution_width,
            min_resolution_height=settings_row.min_resolution_height,
            min_face_size_px=settings_row.min_face_size_px,
            min_sharpness_score=float(settings_row.max_blur_score),
            min_brightness=float(settings_row.min_brightness),
            max_brightness=float(settings_row.max_brightness),
        )
    except (FaceModelUnavailableError, FaceValidationError):
        return []

    if not faces:
        return []

    timestamp = detected_at or _now()
    snapshot_path = _store_snapshot(
        tenant_id=tenant_id,
        camera_id=camera_id,
        image_content=image_content,
        content_type=content_type,
        detected_at=timestamp,
    )
    detections: list[PersonDetection] = []
    for face in faces:
        staff_match = find_best_employee_match(db, tenant_id, face.embedding)
        if staff_match is not None and float(staff_match["confidence"]) < threshold:
            staff_match = None
        visitor_match = find_best_visitor_match(db, tenant_id, face.embedding)
        match_type, matched_staff_id, matched_visitor_id = _choose_match(
            staff_match=staff_match,
            visitor_match=visitor_match,
        )
        existing_detection = _find_recent_duplicate_detection(
            db,
            tenant_id=tenant_id,
            camera_id=camera_id,
            timestamp=timestamp,
            face_embedding=face.embedding,
            match_type=match_type,
            matched_staff_id=matched_staff_id,
            matched_visitor_id=matched_visitor_id,
            threshold=threshold,
        )
        if existing_detection is not None:
            _touch_detected_person(
                existing_detection,
                timestamp=timestamp,
                snapshot_path=snapshot_path,
                quality_score=face.quality_score,
                face_embedding=face.embedding,
                match_type=match_type,
                matched_staff_id=matched_staff_id,
                matched_visitor_id=matched_visitor_id,
            )
            db.add(existing_detection)
            detections.append(existing_detection)
            if existing_detection.match_type == "visitor":
                visitor_id = existing_detection.matched_visitor_id or matched_visitor_id
                if visitor_id is not None:
                    visitor = (
                        db.query(Visitor)
                        .filter(cast(Visitor.id, String) == visitor_id, Visitor.tenant_id == tenant_id)
                        .one_or_none()
                    )
                    if visitor is not None:
                        if visitor.first_seen_at is None:
                            visitor.first_seen_at = timestamp
                        visitor.last_seen_at = timestamp
                        db.add(visitor)
            continue

        detection = PersonDetection(
            tenant_id=tenant_id,
            camera_id=camera_id,
            zone_id=zone_id,
            image_path=snapshot_path,
            detected_at=timestamp,
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            seen_count=1,
            snapshot_quality_score=face.quality_score,
            face_embedding=face.embedding,
            match_type=match_type,
            matched_staff_id=matched_staff_id,
            matched_visitor_id=matched_visitor_id,
            status="new",
        )
        db.add(detection)
        db.flush()
        detections.append(detection)

        if match_type == "visitor" and matched_visitor_id is not None:
            visitor = (
                db.query(Visitor)
                .filter(cast(Visitor.id, String) == matched_visitor_id, Visitor.tenant_id == tenant_id)
                .one_or_none()
            )
            if visitor is not None:
                record_visitor_visit(
                    db,
                    visitor,
                    seen_at=timestamp,
                    person_detection_id=detection.id,
                    camera_id=camera_id,
                    zone_id=zone_id,
                    image_path=snapshot_path,
                    commit=False,
                )

    db.commit()
    for detection in detections:
        db.refresh(detection)
    return detections


def list_person_detections(
    db: Session,
    tenant_id: str,
    *,
    camera_id: str | None = None,
    status: str | None = None,
    match_type: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PersonDetection]:
    query = db.query(PersonDetection).filter(PersonDetection.tenant_id == tenant_id)
    if camera_id:
        query = query.filter(cast(PersonDetection.camera_id, String) == camera_id)
    if status:
        query = query.filter(PersonDetection.status == status)
    if match_type:
        query = query.filter(PersonDetection.match_type == match_type)
    return (
        query.order_by(PersonDetection.last_seen_at.desc(), PersonDetection.detected_at.desc(), PersonDetection.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def list_unknown_review_detections(
    db: Session,
    tenant_id: str,
    *,
    camera_id: str | None = None,
    zone_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[PersonDetection]:
    query = (
        db.query(PersonDetection)
        .filter(
            PersonDetection.tenant_id == tenant_id,
            PersonDetection.match_type == "unknown",
            PersonDetection.note.isnot(None),
        )
    )
    if camera_id:
        query = query.filter(cast(PersonDetection.camera_id, String) == camera_id)
    if zone_id:
        query = query.filter(PersonDetection.zone_id == zone_id)
    if status:
        query = query.filter(PersonDetection.status == status)
    else:
        query = query.filter(PersonDetection.status.in_(["new", "reviewed"]))
    return (
        query.order_by(PersonDetection.last_seen_at.desc(), PersonDetection.detected_at.desc(), PersonDetection.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_person_detection(db: Session, tenant_id: str, detection_id: str) -> PersonDetection | None:
    return (
        db.query(PersonDetection)
        .filter(cast(PersonDetection.id, String) == detection_id, PersonDetection.tenant_id == tenant_id)
        .one_or_none()
    )


def add_note_to_person_detection(
    db: Session,
    tenant_id: str,
    detection_id: str,
    note: str,
) -> PersonDetection | None:
    detection = get_person_detection(db, tenant_id, detection_id)
    if detection is None:
        return None
    detection.note = note.strip()
    if detection.status == "new":
        detection.status = "reviewed"
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def mark_person_detection_reviewed(db: Session, tenant_id: str, detection_id: str) -> PersonDetection | None:
    detection = get_person_detection(db, tenant_id, detection_id)
    if detection is None:
        return None
    detection.status = "reviewed"
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def mark_person_detection_suspicious(db: Session, tenant_id: str, detection_id: str) -> PersonDetection | None:
    detection = get_person_detection(db, tenant_id, detection_id)
    if detection is None:
        return None
    detection.status = "suspicious"
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def ignore_person_detection(db: Session, tenant_id: str, detection_id: str) -> PersonDetection | None:
    detection = get_person_detection(db, tenant_id, detection_id)
    if detection is None:
        return None
    detection.status = "ignored"
    db.add(detection)
    db.commit()
    db.refresh(detection)
    return detection


def add_visitor_from_person_detection(
    db: Session,
    tenant_id: str,
    detection_id: str,
    actor_id: str,
    values: dict,
) -> dict | None:
    try:
        detection = get_person_detection(db, tenant_id, detection_id)
        if detection is None:
            return None
        if detection.match_type != "unknown":
            raise VisitorError("Only unknown detections can be converted to visitors", status_code=422)
        if detection.status == "converted_to_visitor":
            raise VisitorError("Person detection already converted to visitor", status_code=409)

        visitor = None
        visitor_id = values.get("visitor_id")
        if visitor_id:
            visitor = (
                db.query(Visitor)
                .filter(cast(Visitor.id, String) == visitor_id, Visitor.tenant_id == tenant_id)
                .one_or_none()
            )
        if visitor is None:
            visitor = create_visitor(db, tenant_id, actor_id, _prepare_visitor_payload(detection, values), commit=False)
        else:
            visitor.image_path = detection.image_path
            visitor.face_embedding = detection.face_embedding
            if values.get("notes"):
                visitor.notes = f"{visitor.notes}\n{values['notes'].strip()}" if visitor.notes else values["notes"].strip()
            db.add(visitor)
        visit = record_visitor_visit(
            db,
            visitor,
            seen_at=detection.detected_at,
            person_detection_id=detection.id,
            camera_id=detection.camera_id,
            zone_id=detection.zone_id,
            image_path=detection.image_path,
            commit=False,
        )
        detection.matched_visitor_id = visitor.id
        detection.status = "converted_to_visitor"
        detection.match_type = "visitor"
        db.add_all([detection, visitor, visit])
        db.commit()
        db.refresh(visitor)
        db.refresh(visit)
        db.refresh(detection)
        return {
            "visitor": visitor,
            "visit": visit,
            "person_detection": detection,
        }
    except Exception:
        db.rollback()
        raise

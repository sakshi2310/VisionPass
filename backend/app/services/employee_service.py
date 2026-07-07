"""Employee and face enrollment service helpers."""

from __future__ import annotations

import base64
from datetime import datetime, timezone
from statistics import mean
from uuid import uuid4

from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.db.vector import Vector
from app.models.attendance import AttendanceFaceSettings, AttendanceShift
from app.models.employee import AttendanceEmployee, EmployeeFaceEmbedding, EmployeeFaceImage, EmployeeFaceProfile
from app.services.face_ai_service import (
    DUPLICATE_FACE_DETECTED,
    FaceValidationError,
    UploadedFaceImage,
    analyze_face_image,
    successful_validation,
)

FACE_ENROLLMENT_STATUSES = {"Not Enrolled", "Processing", "Enrolled", "Failed"}
DEFAULT_FACE_SETTINGS = {
    "face_match_threshold": app_settings.face_recognition_threshold,
    "min_face_images": 3,
    "recommended_face_images": 5,
    "max_face_images": 10,
    "min_face_size_px": 64,
    "min_resolution_width": 320,
    "min_resolution_height": 240,
    "max_blur_score": 120.0,
    "min_brightness": 35.0,
    "max_brightness": 220.0,
    "embedding_model": app_settings.face_model_name,
    "embedding_version": "v1",
    "embedding_dimension": 512,
    "is_active": True,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def _ensure_employee(db: Session, tenant_id: str, employee_id: str) -> AttendanceEmployee | None:
    return (
        db.query(AttendanceEmployee)
        .filter(AttendanceEmployee.tenant_id == tenant_id, AttendanceEmployee.id == employee_id)
        .one_or_none()
    )


def _ensure_shift_owned(db: Session, tenant_id: str, shift_id: str | None) -> AttendanceShift | None:
    if shift_id is None:
        return None
    return (
        db.query(AttendanceShift)
        .filter(AttendanceShift.tenant_id == tenant_id, AttendanceShift.id == shift_id)
        .one_or_none()
    )


def get_or_create_face_settings(db: Session, tenant_id: str) -> AttendanceFaceSettings:
    settings = (
        db.query(AttendanceFaceSettings)
        .filter(AttendanceFaceSettings.tenant_id == tenant_id)
        .one_or_none()
    )
    if settings is not None:
        return settings

    settings = AttendanceFaceSettings(tenant_id=tenant_id, **DEFAULT_FACE_SETTINGS)
    db.add(settings)
    db.flush()
    return settings


def update_face_settings(
    db: Session,
    tenant_id: str,
    *,
    face_match_threshold: float,
    min_face_images: int,
    recommended_face_images: int,
    max_face_images: int,
    min_face_size_px: int,
    min_resolution_width: int,
    min_resolution_height: int,
    max_blur_score: float,
    min_brightness: float,
    max_brightness: float,
    embedding_model: str,
    embedding_version: str | None,
    embedding_dimension: int,
    is_active: bool,
) -> AttendanceFaceSettings:
    settings = get_or_create_face_settings(db, tenant_id)
    settings.face_match_threshold = face_match_threshold
    settings.min_face_images = min_face_images
    settings.recommended_face_images = recommended_face_images
    settings.max_face_images = max_face_images
    settings.min_face_size_px = min_face_size_px
    settings.min_resolution_width = min_resolution_width
    settings.min_resolution_height = min_resolution_height
    settings.max_blur_score = max_blur_score
    settings.min_brightness = min_brightness
    settings.max_brightness = max_brightness
    settings.embedding_model = embedding_model.strip()
    settings.embedding_version = embedding_version.strip() if embedding_version else None
    settings.embedding_dimension = embedding_dimension
    settings.is_active = is_active
    db.add(settings)
    db.commit()
    db.refresh(settings)
    return settings


def list_employees(
    db: Session,
    tenant_id: str,
    *,
    search: str | None = None,
    department: str | None = None,
    shift_id: str | None = None,
    face_status: str | None = None,
) -> list[AttendanceEmployee]:
    query = db.query(AttendanceEmployee).filter(AttendanceEmployee.tenant_id == tenant_id)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(
            AttendanceEmployee.full_name.ilike(pattern)
            | AttendanceEmployee.employee_code.ilike(pattern)
            | AttendanceEmployee.email.ilike(pattern)
            | AttendanceEmployee.mobile.ilike(pattern)
        )
    if department:
        query = query.filter(AttendanceEmployee.department == department)
    if shift_id:
        query = query.filter(AttendanceEmployee.shift_id == shift_id)

    employees = query.order_by(AttendanceEmployee.created_at.desc()).all()
    if not face_status:
        return employees

    normalized_status = face_status.strip().lower()
    filtered: list[AttendanceEmployee] = []
    for employee in employees:
        profile = get_employee_face_profile(db, tenant_id, employee.id)
        status = _normalize(profile.enrollment_status) if profile else "not enrolled"
        if status == normalized_status:
            filtered.append(employee)
    return filtered


def get_employee(db: Session, tenant_id: str, employee_id: str) -> AttendanceEmployee | None:
    return _ensure_employee(db, tenant_id, employee_id)


def _generate_employee_code(db: Session, tenant_id: str) -> str:
    for _ in range(10):
        code = f"EMP-{uuid4().hex[:8].upper()}"
        exists = (
            db.query(AttendanceEmployee.id)
            .filter(AttendanceEmployee.tenant_id == tenant_id, AttendanceEmployee.employee_code == code)
            .first()
        )
        if exists is None:
            return code
    raise ValueError("Unable to generate a unique employee ID")


def create_employee(
    db: Session,
    tenant_id: str,
    *,
    employee_code: str | None = None,
    full_name: str,
    email: str,
    mobile: str | None = None,
    gender: str | None = None,
    date_of_birth=None,
    department: str | None = None,
    designation: str | None = None,
    shift_id: str | None = None,
    joining_date=None,
    employee_type: str = "Full Time",
    is_active: bool = True,
) -> AttendanceEmployee:
    normalized_code = (employee_code or "").strip() or _generate_employee_code(db, tenant_id)
    normalized_name = full_name.strip()
    normalized_email = email.lower().strip()
    if not normalized_code:
        raise ValueError("Employee code is required")
    if not normalized_name:
        raise ValueError("Full name is required")
    if not normalized_email:
        raise ValueError("Email is required")

    existing_code = (
        db.query(AttendanceEmployee)
        .filter(AttendanceEmployee.tenant_id == tenant_id, AttendanceEmployee.employee_code == normalized_code)
        .one_or_none()
    )
    if existing_code is not None:
        raise ValueError("Employee code already exists for this tenant")

    existing_email = (
        db.query(AttendanceEmployee)
        .filter(AttendanceEmployee.tenant_id == tenant_id, AttendanceEmployee.email == normalized_email)
        .one_or_none()
    )
    if existing_email is not None:
        raise ValueError("Email already exists for this tenant")

    owned_shift = _ensure_shift_owned(db, tenant_id, shift_id)
    if shift_id is not None and owned_shift is None:
        raise ValueError("Assigned shift must belong to the current tenant")

    employee = AttendanceEmployee(
        tenant_id=tenant_id,
        employee_code=normalized_code,
        full_name=normalized_name,
        email=normalized_email,
        mobile=mobile.strip() if mobile else None,
        gender=gender.strip() if gender else None,
        date_of_birth=date_of_birth,
        department=department.strip() if department else None,
        designation=designation.strip() if designation else None,
        shift_id=owned_shift.id if owned_shift is not None else None,
        joining_date=joining_date,
        employee_type=employee_type.strip() if employee_type else "Full Time",
        is_active=is_active,
    )
    db.add(employee)
    db.flush()
    get_or_create_face_settings(db, tenant_id)
    profile = EmployeeFaceProfile(tenant_id=tenant_id, employee_id=employee.id)
    db.add(profile)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(
    db: Session,
    tenant_id: str,
    employee_id: str,
    *,
    employee_code: str | None = None,
    full_name: str | None = None,
    email: str | None = None,
    mobile: str | None = None,
    gender: str | None = None,
    date_of_birth=None,
    department: str | None = None,
    designation: str | None = None,
    shift_id: str | None = None,
    joining_date=None,
    employee_type: str | None = None,
    is_active: bool | None = None,
) -> AttendanceEmployee | None:
    employee = get_employee(db, tenant_id, employee_id)
    if employee is None:
        return None

    if employee_code is not None:
        normalized_code = employee_code.strip()
        if not normalized_code:
            raise ValueError("Employee code is required")
        conflict = (
            db.query(AttendanceEmployee)
            .filter(
                AttendanceEmployee.tenant_id == tenant_id,
                AttendanceEmployee.employee_code == normalized_code,
                AttendanceEmployee.id != employee.id,
            )
            .one_or_none()
        )
        if conflict is not None:
            raise ValueError("Employee code already exists for this tenant")
        employee.employee_code = normalized_code

    if full_name is not None:
        normalized_name = full_name.strip()
        if not normalized_name:
            raise ValueError("Full name is required")
        employee.full_name = normalized_name
    if email is not None:
        normalized_email = email.lower().strip()
        if not normalized_email:
            raise ValueError("Email is required")
        conflict = (
            db.query(AttendanceEmployee)
            .filter(
                AttendanceEmployee.tenant_id == tenant_id,
                AttendanceEmployee.email == normalized_email,
                AttendanceEmployee.id != employee.id,
            )
            .one_or_none()
        )
        if conflict is not None:
            raise ValueError("Email already exists for this tenant")
        employee.email = normalized_email
    if mobile is not None:
        employee.mobile = mobile.strip() or None
    if gender is not None:
        employee.gender = gender.strip() or None
    if date_of_birth is not None:
        employee.date_of_birth = date_of_birth
    if department is not None:
        employee.department = department.strip() or None
    if designation is not None:
        employee.designation = designation.strip() or None
    if shift_id is not None:
        owned_shift = _ensure_shift_owned(db, tenant_id, shift_id)
        if shift_id and owned_shift is None:
            raise ValueError("Assigned shift must belong to the current tenant")
        employee.shift_id = owned_shift.id if owned_shift is not None else None
    if joining_date is not None:
        employee.joining_date = joining_date
    if employee_type is not None:
        employee.employee_type = employee_type.strip() or "Full Time"
    if is_active is not None:
        employee.is_active = is_active

    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, tenant_id: str, employee_id: str) -> bool:
    employee = get_employee(db, tenant_id, employee_id)
    if employee is None:
        return False
    db.delete(employee)
    db.commit()
    return True


def activate_employee(db: Session, tenant_id: str, employee_id: str) -> AttendanceEmployee | None:
    employee = get_employee(db, tenant_id, employee_id)
    if employee is None:
        return None
    employee.is_active = True
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def deactivate_employee(db: Session, tenant_id: str, employee_id: str) -> AttendanceEmployee | None:
    employee = get_employee(db, tenant_id, employee_id)
    if employee is None:
        return None
    employee.is_active = False
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def get_employee_face_profile(db: Session, tenant_id: str, employee_id: str) -> EmployeeFaceProfile | None:
    return (
        db.query(EmployeeFaceProfile)
        .filter(EmployeeFaceProfile.tenant_id == tenant_id, EmployeeFaceProfile.employee_id == employee_id)
        .one_or_none()
    )


def get_employee_face_images(db: Session, tenant_id: str, employee_id: str) -> list[EmployeeFaceImage]:
    return (
        db.query(EmployeeFaceImage)
        .filter(EmployeeFaceImage.tenant_id == tenant_id, EmployeeFaceImage.employee_id == employee_id)
        .order_by(EmployeeFaceImage.created_at.desc())
        .all()
    )


def get_employee_embeddings(db: Session, tenant_id: str, employee_id: str) -> list[EmployeeFaceEmbedding]:
    return (
        db.query(EmployeeFaceEmbedding)
        .filter(EmployeeFaceEmbedding.tenant_id == tenant_id, EmployeeFaceEmbedding.employee_id == employee_id)
        .order_by(EmployeeFaceEmbedding.created_at.desc())
        .all()
    )


def deactivate_employee_embeddings(db: Session, tenant_id: str, employee_id: str) -> int:
    updated = (
        db.query(EmployeeFaceEmbedding)
        .filter(
            EmployeeFaceEmbedding.tenant_id == tenant_id,
            EmployeeFaceEmbedding.employee_id == employee_id,
            EmployeeFaceEmbedding.is_active.is_(True),
        )
        .update({EmployeeFaceEmbedding.is_active: False}, synchronize_session=False)
    )
    db.commit()
    return int(updated or 0)


def _image_data_url(image: UploadedFaceImage) -> str:
    encoded = base64.b64encode(image.content).decode("ascii")
    return f"data:{image.content_type};base64,{encoded}"


def find_duplicate_face(
    db: Session,
    tenant_id: str,
    employee_id: str,
    embedding: list[float],
) -> dict | None:
    """Find the closest active face belonging to another employee in this tenant."""

    statement = text(
        """
        SELECT face.employee_id,
               employee.full_name AS employee_name,
               face.embedding <=> :embedding AS distance,
               1 - (face.embedding <=> :embedding) AS similarity
        FROM employee_face_embeddings AS face
        JOIN attendance_employees AS employee
          ON employee.id = face.employee_id
         AND employee.tenant_id = face.tenant_id
        WHERE face.tenant_id = :tenant_id
          AND face.employee_id <> :employee_id
          AND face.is_active = TRUE
          AND 1 - (face.embedding <=> :embedding) >= :duplicate_threshold
        ORDER BY face.embedding <=> :embedding
        LIMIT 1
        """
    ).bindparams(bindparam("embedding", type_=Vector(512)))
    row = db.execute(
        statement,
        {
            "tenant_id": tenant_id,
            "employee_id": employee_id,
            "embedding": embedding,
            "duplicate_threshold": app_settings.face_duplicate_threshold,
        },
    ).mappings().first()
    if row is None:
        return None
    return {
        "employee_id": str(row["employee_id"]),
        "employee_name": row["employee_name"],
        "distance": float(row["distance"]),
        "similarity": float(row["similarity"]),
    }


def enroll_employee_faces(
    db: Session,
    tenant_id: str,
    employee_id: str,
    images: list[UploadedFaceImage],
    *,
    re_enroll: bool = False,
) -> dict:
    employee = get_employee(db, tenant_id, employee_id)
    if employee is None:
        raise ValueError("Employee not found")

    settings = get_or_create_face_settings(db, tenant_id)
    if len(images) < settings.min_face_images:
        raise ValueError(f"Upload at least {settings.min_face_images} images")
    if len(images) > settings.max_face_images:
        raise ValueError(f"Upload no more than {settings.max_face_images} images")

    profile = get_employee_face_profile(db, tenant_id, employee_id)
    if profile is None:
        profile = EmployeeFaceProfile(tenant_id=tenant_id, employee_id=employee_id)
        db.add(profile)
        db.flush()

    created_images: list[EmployeeFaceImage] = []
    created_embeddings: list[EmployeeFaceEmbedding] = []
    quality_scores: list[float] = []
    validation_results: list[dict] = []
    prior_embeddings_deactivated = False
    for uploaded_image in images:
        try:
            analysis = analyze_face_image(
                uploaded_image.content,
                min_resolution_width=settings.min_resolution_width,
                min_resolution_height=settings.min_resolution_height,
                min_face_size_px=settings.min_face_size_px,
                min_sharpness_score=float(settings.max_blur_score),
                min_brightness=float(settings.min_brightness),
                max_brightness=float(settings.max_brightness),
            )
            validation_result = successful_validation(uploaded_image.filename, analysis)
        except FaceValidationError as exc:
            analysis = None
            validation_result = exc.as_dict(filename=uploaded_image.filename)
        if analysis is not None:
            duplicate = find_duplicate_face(
                db,
                tenant_id,
                employee_id,
                analysis.embedding,
            )
            if duplicate is not None:
                validation_result = {
                    **validation_result,
                    "status": "Rejected",
                    "enrollment_status": "rejected",
                    "code": DUPLICATE_FACE_DETECTED,
                    "message": (
                        "This face is already enrolled for another employee in this tenant."
                    ),
                    "duplicate_employee_id": duplicate["employee_id"],
                    "duplicate_employee_name": duplicate["employee_name"],
                    "duplicate_distance": duplicate["distance"],
                    "duplicate_similarity": duplicate["similarity"],
                }
                analysis = None
        validation_results.append(validation_result)
        if analysis is None:
            continue

        image = EmployeeFaceImage(
            tenant_id=tenant_id,
            employee_id=employee_id,
            image_url=_image_data_url(uploaded_image),
            original_filename=uploaded_image.filename,
            image_type=uploaded_image.content_type,
            quality_score=analysis.quality_score,
            face_detected=True,
            face_count=analysis.face_count,
            validation_status="Validated",
            validation_message=validation_result["message"],
            embedding_generated=False,
        )
        db.add(image)
        db.flush()
        created_images.append(image)
        quality_scores.append(analysis.quality_score)
        if re_enroll and not prior_embeddings_deactivated:
            deactivate_employee_embeddings(db, tenant_id, employee_id)
            prior_embeddings_deactivated = True

        embedding = EmployeeFaceEmbedding(
            tenant_id=tenant_id,
            employee_id=employee_id,
            face_image_id=image.id,
            embedding=analysis.embedding,
            embedding_model=app_settings.face_model_name,
            version=settings.embedding_version,
            quality_score=analysis.quality_score,
            is_active=True,
        )
        db.add(embedding)
        db.flush()
        image.embedding_generated = True
        created_embeddings.append(embedding)

    profile.face_count = db.query(EmployeeFaceImage.id).filter(
        EmployeeFaceImage.tenant_id == tenant_id,
        EmployeeFaceImage.employee_id == employee_id,
    ).count()
    active_embedding_count = db.query(EmployeeFaceEmbedding.id).filter(
        EmployeeFaceEmbedding.tenant_id == tenant_id,
        EmployeeFaceEmbedding.employee_id == employee_id,
        EmployeeFaceEmbedding.is_active.is_(True),
    ).count()
    profile.embedding_count = active_embedding_count
    profile.average_quality_score = mean(quality_scores) if quality_scores else None
    profile.last_enrolled_at = _now() if created_embeddings else profile.last_enrolled_at
    if active_embedding_count:
        profile.enrollment_status = (
            "Enrolled" if active_embedding_count >= settings.min_face_images else "Processing"
        )
    else:
        profile.enrollment_status = "Failed"
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return {
        "profile": profile,
        "images": created_images,
        "embeddings": created_embeddings,
        "validation_results": validation_results,
    }


def re_enroll_employee(db: Session, tenant_id: str, employee_id: str, images: list[UploadedFaceImage]) -> dict:
    return enroll_employee_faces(db, tenant_id, employee_id, images, re_enroll=True)


def update_face_profile_stats(db: Session, tenant_id: str, employee_id: str) -> EmployeeFaceProfile | None:
    profile = get_employee_face_profile(db, tenant_id, employee_id)
    if profile is None:
        return None
    profile.face_count = db.query(EmployeeFaceImage.id).filter(
        EmployeeFaceImage.tenant_id == tenant_id,
        EmployeeFaceImage.employee_id == employee_id,
    ).count()
    profile.embedding_count = db.query(EmployeeFaceEmbedding.id).filter(
        EmployeeFaceEmbedding.tenant_id == tenant_id,
        EmployeeFaceEmbedding.employee_id == employee_id,
        EmployeeFaceEmbedding.is_active.is_(True),
    ).count()
    profile.last_enrolled_at = (
        db.query(EmployeeFaceEmbedding.created_at)
        .filter(
            EmployeeFaceEmbedding.tenant_id == tenant_id,
            EmployeeFaceEmbedding.employee_id == employee_id,
            EmployeeFaceEmbedding.is_active.is_(True),
        )
        .order_by(EmployeeFaceEmbedding.created_at.desc())
        .limit(1)
        .scalar()
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_face_enrollment_summary(db: Session, tenant_id: str) -> dict:
    total_employees = db.query(AttendanceEmployee.id).filter(AttendanceEmployee.tenant_id == tenant_id).count()
    enrolled_employees = (
        db.query(EmployeeFaceProfile.id)
        .filter(EmployeeFaceProfile.tenant_id == tenant_id, EmployeeFaceProfile.enrollment_status == "Enrolled")
        .count()
    )
    in_progress_employees = (
        db.query(EmployeeFaceProfile.id)
        .filter(EmployeeFaceProfile.tenant_id == tenant_id, EmployeeFaceProfile.enrollment_status == "Processing")
        .count()
    )
    failed_employees = (
        db.query(EmployeeFaceProfile.id)
        .filter(EmployeeFaceProfile.tenant_id == tenant_id, EmployeeFaceProfile.enrollment_status == "Failed")
        .count()
    )
    total_images = db.query(EmployeeFaceImage.id).filter(EmployeeFaceImage.tenant_id == tenant_id).count()
    total_embeddings = db.query(EmployeeFaceEmbedding.id).filter(EmployeeFaceEmbedding.tenant_id == tenant_id).count()
    return {
        "total_employees": total_employees,
        "enrolled_employees": enrolled_employees,
        "in_progress_employees": in_progress_employees,
        "failed_employees": failed_employees,
        "total_images": total_images,
        "total_embeddings": total_embeddings,
    }


def search_nearest_face(db: Session, tenant_id: str, input_embedding: list[float]) -> dict | None:
    statement = text(
        """
        SELECT employee_id,
               embedding <=> :input_embedding AS distance
        FROM employee_face_embeddings
        WHERE tenant_id = :tenant_id
          AND is_active = TRUE
        ORDER BY embedding <=> :input_embedding
        LIMIT 1
        """
    ).bindparams(bindparam("input_embedding", type_=Vector(512)))
    row = db.execute(statement, {"tenant_id": tenant_id, "input_embedding": input_embedding}).mappings().first()
    if row is None:
        return None
    return {"employee_id": row["employee_id"], "distance": float(row["distance"])}

"""Common staff routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.dependencies import database_session, get_current_tenant_admin
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeFaceEmbeddingRead,
    EmployeeFaceEnrollmentResponse,
    EmployeeFaceImageListResponse,
    EmployeeFaceImageRead,
    EmployeeFaceProfileRead,
    EmployeeListResponse,
    EmployeeRead,
    EmployeeUpdate,
    FaceImageValidationResult,
)
from app.services.employee_service import (
    activate_employee,
    create_employee,
    deactivate_employee,
    delete_employee,
    enroll_employee_faces,
    get_employee,
    get_employee_embeddings,
    get_employee_face_images,
    get_employee_face_profile,
    list_employees,
    update_employee,
)
from app.services.face_ai_service import FaceModelUnavailableError, UploadedFaceImage

router = APIRouter()


async def _read_face_uploads(files: list[UploadFile]) -> list[UploadedFaceImage]:
    max_bytes = app_settings.upload_max_image_mb * 1024 * 1024
    uploads: list[UploadedFaceImage] = []
    for upload in files:
        content_type = (upload.content_type or "").lower()
        filename = Path(upload.filename or "face-image").name
        if not content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "INVALID_IMAGE",
                    "message": f"{filename} is not an image file.",
                    "validation_results": [],
                },
            )
        content = await upload.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "code": "INVALID_IMAGE",
                    "message": f"{filename} exceeds the {app_settings.upload_max_image_mb} MB upload limit.",
                    "validation_results": [],
                },
            )
        uploads.append(
            UploadedFaceImage(
                content=content,
                filename=filename,
                content_type=content_type,
            )
        )
    return uploads


def _face_enrollment_response(result: dict) -> EmployeeFaceEnrollmentResponse:
    validation_results = [FaceImageValidationResult.model_validate(item) for item in result["validation_results"]]
    if not result["embeddings"]:
        first_failure = next(
            (item for item in result["validation_results"] if item.get("code")),
            {
                "code": "LOW_IMAGE_QUALITY",
                "message": "No image passed face enrollment validation.",
            },
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": first_failure["code"],
                "message": first_failure["message"],
                "validation_results": result["validation_results"],
            },
        )
    return EmployeeFaceEnrollmentResponse(
        profile=EmployeeFaceProfileRead.model_validate(result["profile"]),
        images=[EmployeeFaceImageRead.model_validate(image) for image in result["images"]],
        embeddings=[EmployeeFaceEmbeddingRead.model_validate(embedding) for embedding in result["embeddings"]],
        validation_results=validation_results,
    )


@router.get("", response_model=EmployeeListResponse)
def read_staff(
    search: str | None = Query(default=None),
    department: str | None = Query(default=None),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeListResponse:
    staff = list_employees(
        db,
        current_admin.tenant_id,
        search=search,
        department=department,
    )
    return EmployeeListResponse(employees=[EmployeeRead.model_validate(employee) for employee in staff])


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_staff_member(
    payload: EmployeeCreate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    try:
        employee = create_employee(
            db,
            current_admin.tenant_id,
            employee_code=payload.employee_code,
            full_name=payload.full_name,
            email=payload.email,
            mobile=payload.mobile,
            gender=payload.gender,
            date_of_birth=payload.date_of_birth,
            department=payload.department,
            designation=payload.designation,
            shift_id=payload.shift_id,
            joining_date=payload.joining_date,
            employee_type=payload.employee_type,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return EmployeeRead.model_validate(employee)


@router.get("/{staff_id}", response_model=EmployeeRead)
def read_staff_member(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = get_employee(db, current_admin.tenant_id, staff_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return EmployeeRead.model_validate(employee)


@router.patch("/{staff_id}", response_model=EmployeeRead)
def update_staff_member(
    staff_id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    try:
        employee = update_employee(
            db,
            current_admin.tenant_id,
            staff_id,
            employee_code=payload.employee_code,
            full_name=payload.full_name,
            email=payload.email,
            mobile=payload.mobile,
            gender=payload.gender,
            date_of_birth=payload.date_of_birth,
            department=payload.department,
            designation=payload.designation,
            shift_id=payload.shift_id,
            joining_date=payload.joining_date,
            employee_type=payload.employee_type,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return EmployeeRead.model_validate(employee)


@router.patch("/{staff_id}/activate", response_model=EmployeeRead)
def activate_staff_member(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = activate_employee(db, current_admin.tenant_id, staff_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return EmployeeRead.model_validate(employee)


@router.patch("/{staff_id}/deactivate", response_model=EmployeeRead)
def deactivate_staff_member(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = deactivate_employee(db, current_admin.tenant_id, staff_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")
    return EmployeeRead.model_validate(employee)


@router.delete("/{staff_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_staff_member(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_employee(db, current_admin.tenant_id, staff_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff not found")


@router.get("/{staff_id}/face-profile", response_model=EmployeeFaceProfileRead)
def read_staff_face_profile(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceProfileRead:
    profile = get_employee_face_profile(db, current_admin.tenant_id, staff_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face profile not found")
    return EmployeeFaceProfileRead.model_validate(profile)


@router.get("/{staff_id}/face-images", response_model=EmployeeFaceImageListResponse)
def read_staff_face_images(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceImageListResponse:
    images = get_employee_face_images(db, current_admin.tenant_id, staff_id)
    return EmployeeFaceImageListResponse(images=[EmployeeFaceImageRead.model_validate(image) for image in images])


@router.get("/{staff_id}/face-embeddings", response_model=EmployeeFaceEnrollmentResponse)
def read_staff_face_embeddings(
    staff_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceEnrollmentResponse:
    embeddings = get_employee_embeddings(db, current_admin.tenant_id, staff_id)
    profile = get_employee_face_profile(db, current_admin.tenant_id, staff_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face profile not found")
    return EmployeeFaceEnrollmentResponse(
        profile=EmployeeFaceProfileRead.model_validate(profile),
        images=[],
        embeddings=[EmployeeFaceEmbeddingRead.model_validate(embedding) for embedding in embeddings],
        validation_results=[],
    )


@router.post("/{staff_id}/face-images", response_model=EmployeeFaceEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_staff_face_images(
    staff_id: str,
    files: list[UploadFile] = File(...),
    re_enroll: bool = Form(False),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceEnrollmentResponse:
    try:
        uploads = await _read_face_uploads(files)
        result = enroll_employee_faces(
            db,
            current_admin.tenant_id,
            staff_id,
            uploads,
            re_enroll=re_enroll,
        )
    except FaceModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _face_enrollment_response(result)

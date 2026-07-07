"""Client admin attendance routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.core.dependencies import database_session, get_current_tenant_admin, require_module
from app.schemas.attendance import (
    AttendanceFaceSettingsRead,
    AttendanceFaceSettingsUpdate,
    AttendanceHolidayCreate,
    AttendanceHolidayListResponse,
    AttendanceHolidayRead,
    AttendanceHolidayUpdate,
    AttendanceSettingsBundleResponse,
    AttendanceSettingsRead,
    AttendanceSettingsUpdate,
    AttendanceShiftCreate,
    AttendanceShiftListResponse,
    AttendanceShiftRead,
    AttendanceShiftUpdate,
    AttendanceWorkingDayRead,
)
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeFaceEmbeddingListResponse,
    EmployeeFaceEmbeddingRead,
    EmployeeFaceEnrollmentResponse,
    EmployeeFaceEnrollmentSummary,
    EmployeeFaceImageListResponse,
    EmployeeFaceImageRead,
    EmployeeFaceProfileRead,
    EmployeeListResponse,
    EmployeeRead,
    EmployeeStatusUpdate,
    EmployeeUpdate,
    FaceImageValidationResult,
)
from app.services.attendance_service import (
    get_attendance_board,
    get_employee_attendance_summary,
    create_holiday,
    create_shift,
    delete_holiday,
    delete_shift,
    get_attendance_settings_bundle,
    get_holiday,
    get_shift,
    list_holidays,
    list_shifts,
    set_default_shift,
    update_attendance_settings,
    update_holiday,
    update_shift,
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
    get_face_enrollment_summary,
    get_or_create_face_settings,
    list_employees,
    re_enroll_employee,
    update_employee,
    update_face_settings,
)
from app.services.face_ai_service import FaceModelUnavailableError, UploadedFaceImage

router = APIRouter(dependencies=[Depends(require_module("attendance"))])


@router.get("/settings", response_model=AttendanceSettingsBundleResponse)
def read_settings(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceSettingsBundleResponse:
    bundle = get_attendance_settings_bundle(db, current_admin.tenant_id)
    return AttendanceSettingsBundleResponse(
        attendance_settings=AttendanceSettingsRead.model_validate(bundle["attendance_settings"]),
        working_days=[AttendanceWorkingDayRead.model_validate(day) for day in bundle["working_days"]],
    )


@router.put("/settings", response_model=AttendanceSettingsBundleResponse)
def save_settings(
    payload: AttendanceSettingsUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceSettingsBundleResponse:
    try:
        bundle = update_attendance_settings(
            db,
            current_admin.tenant_id,
            duplicate_detection_cooldown_minutes=payload.duplicate_detection_cooldown_minutes,
            allow_manual_correction=payload.allow_manual_correction,
            require_correction_reason=payload.require_correction_reason,
            timezone=payload.timezone,
            working_days=payload.working_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AttendanceSettingsBundleResponse(
        attendance_settings=AttendanceSettingsRead.model_validate(bundle["attendance_settings"]),
        working_days=[AttendanceWorkingDayRead.model_validate(day) for day in bundle["working_days"]],
    )


@router.get("/shifts", response_model=AttendanceShiftListResponse)
def read_shifts(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceShiftListResponse:
    shifts = list_shifts(db, current_admin.tenant_id)
    return AttendanceShiftListResponse(shifts=[AttendanceShiftRead.model_validate(shift) for shift in shifts])


@router.post("/shifts", response_model=AttendanceShiftRead, status_code=status.HTTP_201_CREATED)
def add_shift(
    payload: AttendanceShiftCreate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceShiftRead:
    try:
        shift = create_shift(
            db,
            current_admin.tenant_id,
            name=payload.name,
            start_time=payload.start_time,
            end_time=payload.end_time,
            grace_period_minutes=payload.grace_period_minutes,
            late_after_minutes=payload.late_after_minutes,
            half_day_min_minutes=payload.half_day_min_minutes,
            full_day_min_minutes=payload.full_day_min_minutes,
            auto_checkout_time=payload.auto_checkout_time,
            break_duration_minutes=payload.break_duration_minutes,
            is_default=payload.is_default,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AttendanceShiftRead.model_validate(shift)


@router.get("/shifts/{shift_id}", response_model=AttendanceShiftRead)
def read_shift(
    shift_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceShiftRead:
    shift = get_shift(db, current_admin.tenant_id, shift_id)
    if shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return AttendanceShiftRead.model_validate(shift)


@router.put("/shifts/{shift_id}", response_model=AttendanceShiftRead)
def save_shift(
    shift_id: str,
    payload: AttendanceShiftUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceShiftRead:
    try:
        shift = update_shift(
            db,
            current_admin.tenant_id,
            shift_id,
            name=payload.name,
            start_time=payload.start_time,
            end_time=payload.end_time,
            grace_period_minutes=payload.grace_period_minutes,
            late_after_minutes=payload.late_after_minutes,
            half_day_min_minutes=payload.half_day_min_minutes,
            full_day_min_minutes=payload.full_day_min_minutes,
            auto_checkout_time=payload.auto_checkout_time,
            break_duration_minutes=payload.break_duration_minutes,
            is_default=payload.is_default,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return AttendanceShiftRead.model_validate(shift)


@router.delete("/shifts/{shift_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_shift(
    shift_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_shift(db, current_admin.tenant_id, shift_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")


@router.patch("/shifts/{shift_id}/default", response_model=AttendanceShiftRead)
def make_default_shift(
    shift_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceShiftRead:
    shift = set_default_shift(db, current_admin.tenant_id, shift_id)
    if shift is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shift not found")
    return AttendanceShiftRead.model_validate(shift)


@router.get("/holidays", response_model=AttendanceHolidayListResponse)
def read_holidays(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceHolidayListResponse:
    holidays = list_holidays(db, current_admin.tenant_id)
    return AttendanceHolidayListResponse(holidays=[AttendanceHolidayRead.model_validate(holiday) for holiday in holidays])


@router.post("/holidays", response_model=AttendanceHolidayRead, status_code=status.HTTP_201_CREATED)
def add_holiday(
    payload: AttendanceHolidayCreate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceHolidayRead:
    try:
        holiday = create_holiday(
            db,
            current_admin.tenant_id,
            holiday_name=payload.holiday_name,
            holiday_date=payload.holiday_date,
            department_id=payload.department_id,
            location_id=payload.location_id,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return AttendanceHolidayRead.model_validate(holiday)


@router.put("/holidays/{holiday_id}", response_model=AttendanceHolidayRead)
def save_holiday(
    holiday_id: str,
    payload: AttendanceHolidayUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceHolidayRead:
    try:
        holiday = update_holiday(
            db,
            current_admin.tenant_id,
            holiday_id,
            holiday_name=payload.holiday_name,
            holiday_date=payload.holiday_date,
            department_id=payload.department_id,
            location_id=payload.location_id,
            is_active=payload.is_active,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if holiday is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")
    return AttendanceHolidayRead.model_validate(holiday)


@router.delete("/holidays/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_holiday(
    holiday_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_holiday(db, current_admin.tenant_id, holiday_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Holiday not found")



@router.get("/board")
def read_attendance_board(
    date: str | None = Query(default=None),
    search: str | None = Query(default=None),
    department: str | None = Query(default=None),
    shift_id: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> dict:
    try:
        return get_attendance_board(
            db,
            current_admin.tenant_id,
            attendance_date=date,
            search=search,
            department=department,
            shift_id=shift_id,
            status_filter=status_filter,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/board/{employee_id}")
def read_employee_attendance_summary(
    employee_id: str,
    date: str | None = Query(default=None),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> dict:
    try:
        summary = get_employee_attendance_summary(
            db,
            current_admin.tenant_id,
            employee_id,
            attendance_date=date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    if summary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return summary


@router.get("/employees", response_model=EmployeeListResponse)
def read_employees(
    search: str | None = Query(default=None),
    department: str | None = Query(default=None),
    shift_id: str | None = Query(default=None),
    face_status: str | None = Query(default=None),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeListResponse:
    employees = list_employees(
        db,
        current_admin.tenant_id,
        search=search,
        department=department,
        shift_id=shift_id,
        face_status=face_status,
    )
    return EmployeeListResponse(employees=[EmployeeRead.model_validate(employee) for employee in employees])


@router.post("/employees", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def add_employee(
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


@router.get("/employees/{employee_id}", response_model=EmployeeRead)
def read_employee(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = get_employee(db, current_admin.tenant_id, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeRead.model_validate(employee)


@router.put("/employees/{employee_id}", response_model=EmployeeRead)
def save_employee(
    employee_id: str,
    payload: EmployeeUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    try:
        employee = update_employee(
            db,
            current_admin.tenant_id,
            employee_id,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeRead.model_validate(employee)


@router.patch("/employees/{employee_id}/activate", response_model=EmployeeRead)
def activate_employee_route(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = activate_employee(db, current_admin.tenant_id, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeRead.model_validate(employee)


@router.patch("/employees/{employee_id}/deactivate", response_model=EmployeeRead)
def deactivate_employee_route(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeRead:
    employee = deactivate_employee(db, current_admin.tenant_id, employee_id)
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return EmployeeRead.model_validate(employee)


@router.delete("/employees/{employee_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_employee(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_employee(db, current_admin.tenant_id, employee_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")


@router.get("/employees/{employee_id}/face-profile", response_model=EmployeeFaceProfileRead)
def read_employee_face_profile(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceProfileRead:
    profile = get_employee_face_profile(db, current_admin.tenant_id, employee_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face profile not found")
    return EmployeeFaceProfileRead.model_validate(profile)


@router.get("/employees/{employee_id}/face-images", response_model=EmployeeFaceImageListResponse)
def read_employee_face_images(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceImageListResponse:
    images = get_employee_face_images(db, current_admin.tenant_id, employee_id)
    return EmployeeFaceImageListResponse(images=[EmployeeFaceImageRead.model_validate(image) for image in images])


@router.get("/employees/{employee_id}/face-embeddings", response_model=EmployeeFaceEmbeddingListResponse)
def read_employee_face_embeddings(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceEmbeddingListResponse:
    embeddings = get_employee_embeddings(db, current_admin.tenant_id, employee_id)
    return EmployeeFaceEmbeddingListResponse(embeddings=[EmployeeFaceEmbeddingRead.model_validate(embedding) for embedding in embeddings])


@router.get("/face-enrollment/summary", response_model=EmployeeFaceEnrollmentSummary)
def read_face_enrollment_summary(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceEnrollmentSummary:
    return EmployeeFaceEnrollmentSummary.model_validate(get_face_enrollment_summary(db, current_admin.tenant_id))


@router.get("/face-settings", response_model=AttendanceFaceSettingsRead)
def read_face_settings(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceFaceSettingsRead:
    settings = get_or_create_face_settings(db, current_admin.tenant_id)
    return AttendanceFaceSettingsRead.model_validate(settings)


@router.put("/face-settings", response_model=AttendanceFaceSettingsRead)
def save_face_settings(
    payload: AttendanceFaceSettingsUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AttendanceFaceSettingsRead:
    settings = update_face_settings(
        db,
        current_admin.tenant_id,
        face_match_threshold=payload.face_match_threshold,
        min_face_images=payload.min_face_images,
        recommended_face_images=payload.recommended_face_images,
        max_face_images=payload.max_face_images,
        min_face_size_px=payload.min_face_size_px,
        min_resolution_width=payload.min_resolution_width,
        min_resolution_height=payload.min_resolution_height,
        max_blur_score=payload.max_blur_score,
        min_brightness=payload.min_brightness,
        max_brightness=payload.max_brightness,
        embedding_model=payload.embedding_model,
        embedding_version=payload.embedding_version,
        embedding_dimension=payload.embedding_dimension,
        is_active=payload.is_active,
    )
    return AttendanceFaceSettingsRead.model_validate(settings)


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
                    "message": (
                        f"{filename} exceeds the {app_settings.upload_max_image_mb} MB upload limit."
                    ),
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
    validation_results = [
        FaceImageValidationResult.model_validate(item)
        for item in result["validation_results"]
    ]
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


@router.post("/employees/{employee_id}/face-images", response_model=EmployeeFaceEnrollmentResponse, status_code=status.HTTP_201_CREATED)
async def upload_employee_face_images(
    employee_id: str,
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
            employee_id,
            uploads,
            re_enroll=re_enroll,
        )
    except FaceModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _face_enrollment_response(result)


@router.post("/employees/{employee_id}/generate-embeddings", response_model=EmployeeFaceEnrollmentResponse)
async def generate_employee_face_embeddings(
    employee_id: str,
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
            employee_id,
            uploads,
            re_enroll=re_enroll,
        )
    except FaceModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _face_enrollment_response(result)


@router.post("/employees/{employee_id}/re-enroll-face", response_model=EmployeeFaceEnrollmentResponse)
async def re_enroll_employee_face(
    employee_id: str,
    files: list[UploadFile] = File(...),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> EmployeeFaceEnrollmentResponse:
    try:
        uploads = await _read_face_uploads(files)
        result = re_enroll_employee(db, current_admin.tenant_id, employee_id, uploads)
    except FaceModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _face_enrollment_response(result)


@router.delete("/employees/{employee_id}/face-enrollment", status_code=status.HTTP_204_NO_CONTENT)
def delete_employee_face_enrollment(
    employee_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    profile = get_employee_face_profile(db, current_admin.tenant_id, employee_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Face profile not found")
    from app.models.employee import EmployeeFaceEmbedding, EmployeeFaceImage

    db.query(EmployeeFaceEmbedding).filter(
        EmployeeFaceEmbedding.tenant_id == current_admin.tenant_id,
        EmployeeFaceEmbedding.employee_id == employee_id,
    ).update({EmployeeFaceEmbedding.is_active: False}, synchronize_session=False)
    db.query(EmployeeFaceImage).filter(
        EmployeeFaceImage.tenant_id == current_admin.tenant_id,
        EmployeeFaceImage.employee_id == employee_id,
    ).delete(synchronize_session=False)
    profile.enrollment_status = "Not Enrolled"
    profile.face_count = 0
    profile.embedding_count = 0
    profile.average_quality_score = None
    profile.last_enrolled_at = None
    db.add(profile)
    db.commit()

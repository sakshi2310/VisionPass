"""Employee and face enrollment schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings


class EmployeeBase(BaseModel):
    employee_code: str
    full_name: str
    email: str
    mobile: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    department: str | None = None
    designation: str | None = None
    shift_id: str | None = None
    joining_date: date | None = None
    employee_type: str = "Full Time"
    is_active: bool = True


class EmployeeRead(EmployeeBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeListResponse(BaseModel):
    employees: list[EmployeeRead] = Field(default_factory=list)


class EmployeeCreate(EmployeeBase):
    employee_code: str | None = None


class EmployeePortalAccountRead(BaseModel):
    user_id: str
    email: str
    role: str = "user"
    temporary_password: str | None = None
    created: bool = False


class EmployeeCreateResponse(BaseModel):
    employee: EmployeeRead
    portal_account: EmployeePortalAccountRead | None = None


class EmployeeUpdate(BaseModel):
    employee_code: str | None = None
    full_name: str | None = None
    email: str | None = None
    mobile: str | None = None
    gender: str | None = None
    date_of_birth: date | None = None
    department: str | None = None
    designation: str | None = None
    shift_id: str | None = None
    joining_date: date | None = None
    employee_type: str | None = None
    is_active: bool | None = None


class EmployeeStatusUpdate(BaseModel):
    is_active: bool


class EmployeeFaceProfileRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    enrollment_status: str
    face_count: int
    embedding_count: int
    average_quality_score: float | None = None
    last_enrolled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeFaceImageRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    image_url: str
    original_filename: str | None = None
    image_type: str | None = None
    quality_score: float | None = None
    face_detected: bool
    face_count: int
    validation_status: str
    validation_message: str | None = None
    embedding_generated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeFaceImageListResponse(BaseModel):
    images: list[EmployeeFaceImageRead] = Field(default_factory=list)


class EmployeeFaceEmbeddingRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    face_image_id: str | None = None
    embedding_model: str
    version: str | None = None
    quality_score: float | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeFaceEmbeddingListResponse(BaseModel):
    embeddings: list[EmployeeFaceEmbeddingRead] = Field(default_factory=list)


class EmployeeFaceEnrollmentSummary(BaseModel):
    total_employees: int = 0
    enrolled_employees: int = 0
    in_progress_employees: int = 0
    failed_employees: int = 0
    total_images: int = 0
    total_embeddings: int = 0


class FaceImageValidationResult(BaseModel):
    filename: str | None = None
    status: str
    enrollment_status: str
    code: str | None = None
    message: str
    detection_confidence: float | None = None
    quality_score: float | None = None
    width: int | None = None
    height: int | None = None
    face_count: int | None = None
    face_bbox: tuple[int, int, int, int] | None = None
    face_size_px: int | None = None
    blur_score: float | None = None
    brightness: float | None = None
    duplicate_employee_id: str | None = None
    duplicate_employee_name: str | None = None
    duplicate_distance: float | None = None
    duplicate_similarity: float | None = None


class EmployeeFaceEnrollmentResponse(BaseModel):
    profile: EmployeeFaceProfileRead
    images: list[EmployeeFaceImageRead] = Field(default_factory=list)
    embeddings: list[EmployeeFaceEmbeddingRead] = Field(default_factory=list)
    validation_results: list[FaceImageValidationResult] = Field(default_factory=list)


class FaceSettingsRead(BaseModel):
    id: str
    tenant_id: str
    face_match_threshold: float
    min_face_images: int
    recommended_face_images: int
    max_face_images: int
    min_face_size_px: int
    min_resolution_width: int
    min_resolution_height: int
    max_blur_score: float
    min_brightness: float
    max_brightness: float
    embedding_model: str
    embedding_version: str | None = None
    embedding_dimension: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FaceSettingsUpdate(BaseModel):
    face_match_threshold: float = Field(
        default_factory=lambda: settings.face_recognition_threshold, ge=0, le=1
    )
    min_face_images: int = Field(default=3, ge=1)
    recommended_face_images: int = Field(default=5, ge=1)
    max_face_images: int = Field(default=10, ge=1)
    min_face_size_px: int = Field(default=64, ge=1)
    min_resolution_width: int = Field(default=320, ge=1)
    min_resolution_height: int = Field(default=240, ge=1)
    max_blur_score: float = Field(default=120.0, ge=0)
    min_brightness: float = Field(default=35.0, ge=0)
    max_brightness: float = Field(default=220.0, ge=0)
    embedding_model: str = Field(default_factory=lambda: settings.face_model_name, min_length=1)
    embedding_version: str | None = None
    embedding_dimension: int = Field(default=512, ge=1)
    is_active: bool = True


class FaceSettingsResponse(BaseModel):
    face_settings: FaceSettingsRead

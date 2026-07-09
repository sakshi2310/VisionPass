"""Attendance schemas."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.config import settings
from app.schemas.recognition import RecognitionResponse


class AttendanceWorkingDayRead(BaseModel):
    id: str
    tenant_id: str
    day_of_week: int
    is_working: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceSettingsRead(BaseModel):
    id: str
    tenant_id: str
    duplicate_detection_cooldown_minutes: int
    allow_manual_correction: bool
    require_correction_reason: bool
    timezone: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceSettingsUpdate(BaseModel):
    duplicate_detection_cooldown_minutes: int = Field(
        default_factory=lambda: settings.attendance_duplicate_cooldown_minutes, ge=1
    )
    allow_manual_correction: bool = True
    require_correction_reason: bool = True
    timezone: str = Field(default="Asia/Kolkata", min_length=1)
    working_days: list[int] = Field(default_factory=list)

    @field_validator("working_days")
    @classmethod
    def normalize_working_days(cls, value: list[int]) -> list[int]:
        normalized = sorted({int(day) for day in value})
        invalid = [day for day in normalized if day < 0 or day > 6]
        if invalid:
            raise ValueError("working_days must only contain values from 0 to 6")
        if not normalized:
            raise ValueError("At least one working day must be selected")
        return normalized


class AttendanceSettingsBundleResponse(BaseModel):
    attendance_settings: AttendanceSettingsRead
    working_days: list[AttendanceWorkingDayRead] = Field(default_factory=list)


class AttendanceFaceSettingsRead(BaseModel):
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


class AttendanceFaceSettingsUpdate(BaseModel):
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


class AttendanceShiftBase(BaseModel):
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int = Field(
        default_factory=lambda: settings.attendance_late_grace_minutes, ge=0
    )
    late_after_minutes: int = Field(
        default_factory=lambda: settings.attendance_late_grace_minutes, ge=0
    )
    half_day_min_minutes: int = Field(ge=1)
    full_day_min_minutes: int = Field(ge=1)
    auto_checkout_time: str | None = None
    break_duration_minutes: int = Field(default=0, ge=0)
    is_default: bool = False
    is_active: bool = True


class AttendanceShiftCreate(AttendanceShiftBase):
    pass


class AttendanceShiftUpdate(BaseModel):
    name: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    grace_period_minutes: int | None = Field(default=None, ge=0)
    late_after_minutes: int | None = Field(default=None, ge=0)
    half_day_min_minutes: int | None = Field(default=None, ge=1)
    full_day_min_minutes: int | None = Field(default=None, ge=1)
    auto_checkout_time: str | None = None
    break_duration_minutes: int | None = Field(default=None, ge=0)
    is_default: bool | None = None
    is_active: bool | None = None


class AttendanceShiftRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int
    late_after_minutes: int
    half_day_min_minutes: int
    full_day_min_minutes: int
    auto_checkout_time: time | None
    break_duration_minutes: int
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceShiftListResponse(BaseModel):
    shifts: list[AttendanceShiftRead] = Field(default_factory=list)


class AttendanceHolidayBase(BaseModel):
    holiday_name: str
    holiday_date: date
    department_id: str | None = None
    location_id: str | None = None
    is_active: bool = True


class AttendanceHolidayCreate(AttendanceHolidayBase):
    pass


class AttendanceHolidayUpdate(BaseModel):
    holiday_name: str | None = None
    holiday_date: date | None = None
    department_id: str | None = None
    location_id: str | None = None
    is_active: bool | None = None


class AttendanceHolidayRead(BaseModel):
    id: str
    tenant_id: str
    holiday_name: str
    holiday_date: date
    department_id: str | None
    location_id: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceHolidayListResponse(BaseModel):
    holidays: list[AttendanceHolidayRead] = Field(default_factory=list)


class AttendanceMarkRequest(BaseModel):
    employee_id: str
    source: Literal["camera", "manual", "web"] = "manual"
    camera_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    event_time: datetime | None = None
    metadata: dict = Field(default_factory=dict)


class AttendanceEventRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    event_type: Literal["check_in", "check_out"]
    source: Literal["camera", "manual", "web"]
    camera_id: str | None = None
    confidence: float | None = None
    event_time: datetime
    metadata: dict = Field(validation_alias="event_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DailyAttendanceRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    attendance_date: date
    first_check_in: datetime | None = None
    last_check_out: datetime | None = None
    total_work_minutes: int
    status: Literal["present", "late", "half_day", "absent", "holiday"]
    shift_id: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendancePresenceSessionRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str
    attendance_date: date
    session_type: Literal["present", "absent"]
    started_at: datetime
    ended_at: datetime | None = None
    latest_source: str | None = None
    camera_id: str | None = None
    reason: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceMarkResponse(BaseModel):
    event: AttendanceEventRead
    daily: DailyAttendanceRead
    employee_id: str
    employee_name: str
    employee_code: str
    message: str


class TodayAttendanceItem(DailyAttendanceRead):
    employee_name: str
    employee_code: str


class TodayAttendanceResponse(BaseModel):
    records: list[TodayAttendanceItem] = Field(default_factory=list)


class RecognizeAndMarkResponse(BaseModel):
    recognition: RecognitionResponse
    attendance: AttendanceMarkResponse | None = None

"""Authenticated tenant-user self-service schemas."""

from __future__ import annotations

from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, Field

AttendanceStatus = Literal["present", "late", "half_day", "absent", "holiday", "not_marked"]


class MeShift(BaseModel):
    id: str
    name: str
    start_time: time
    end_time: time
    grace_period_minutes: int


class MeMonthlySummary(BaseModel):
    month: str
    present: int = 0
    late: int = 0
    half_day: int = 0
    absent: int = 0
    holidays: int = 0
    total_working_days: int = 0
    total_work_hours: float = 0
    attendance_percentage: float = 0


class MeDashboardResponse(BaseModel):
    today_status: AttendanceStatus
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
    working_hours: float = 0
    current_shift: MeShift | None = None
    monthly_summary: MeMonthlySummary
    employee_linked: bool


class MeAttendanceDay(BaseModel):
    id: str
    attendance_date: date
    first_check_in: datetime | None = None
    last_check_out: datetime | None = None
    total_work_minutes: int
    working_hours: float
    status: AttendanceStatus
    shift: MeShift | None = None


class MeAttendanceResponse(BaseModel):
    month: str
    days: list[MeAttendanceDay] = Field(default_factory=list)
    summary: MeMonthlySummary
    employee_linked: bool


class MeProfileResponse(BaseModel):
    member_id: str
    employee_id: str | None = None
    full_name: str
    email: str
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    employee_code: str | None = None
    employee_type: str | None = None
    joining_date: date | None = None
    status: str
    shift: MeShift | None = None
    face_enrollment_status: str
    face_count: int = 0


class MeNotification(BaseModel):
    id: str
    type: Literal["attendance", "profile"]
    title: str
    message: str
    severity: Literal["info", "warning"]
    created_at: datetime


class MeNotificationsResponse(BaseModel):
    notifications: list[MeNotification] = Field(default_factory=list)

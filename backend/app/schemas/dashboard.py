"""Client-admin dashboard response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ClientAdminDashboardSummary(BaseModel):
    total_employees: int = 0
    active_employees: int = 0
    today_present: int = 0
    today_absent: int = 0
    today_late: int = 0
    active_cameras: int = 0
    offline_cameras: int = 0
    unknown_face_alerts: int = 0


class AttendanceLiveCameraStatus(BaseModel):
    camera_id: str | None = None
    camera_name: str | None = None
    enabled: bool = False
    health_status: str = "unknown"
    last_frame_at: datetime | None = None


class AttendanceBoardStats(BaseModel):
    total: int = 0
    present: int = 0
    late: int = 0
    half_day: int = 0
    absent: int = 0
    holiday: int = 0
    not_detected: int = 0
    unknown_face_attempts: int = 0


class DashboardAttendanceEvent(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    employee_code: str
    event_type: str
    source: str
    camera_id: str | None = None
    camera_name: str | None = None
    confidence: float | None = None
    event_time: datetime


class AttendanceLatestSession(BaseModel):
    employee_id: str
    employee_code: str
    employee_name: str
    latest_event_type: str | None = None
    latest_event_time: datetime | None = None
    source: str | None = None
    status: str
    work_minutes: int = 0
    reason: str | None = None
    remarks: str | None = None
    camera_id: str | None = None
    camera_name: str | None = None


class DashboardRecognitionAttempt(BaseModel):
    id: str
    camera_id: str
    camera_name: str
    employee_id: str | None = None
    employee_name: str | None = None
    recognition_status: str
    confidence: float | None = None
    created_at: datetime


class ClientAdminRecentActivity(BaseModel):
    attendance_events: list[DashboardAttendanceEvent] = Field(default_factory=list)
    recognition_attempts: list[DashboardRecognitionAttempt] = Field(default_factory=list)

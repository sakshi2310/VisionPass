"""Tenant-scoped client-admin dashboard queries."""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import String, cast, distinct, func
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceEvent, AttendanceSettings, DailyAttendanceRecord
from app.models.alert import Alert
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee

PRESENT_STATUSES = ("present", "late", "half_day")
OFFLINE_STATUSES = ("offline", "error")


def _tenant_today(db: Session, tenant_id: str) -> date:
    timezone_name = (
        db.query(AttendanceSettings.timezone)
        .filter(AttendanceSettings.tenant_id == tenant_id)
        .scalar()
        or "Asia/Kolkata"
    )
    try:
        tenant_zone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        tenant_zone = ZoneInfo("Asia/Kolkata")

    return datetime.now(tenant_zone).date()


def get_dashboard_summary(db: Session, tenant_id: str) -> dict[str, int]:
    tenant_date = _tenant_today(db, tenant_id)

    total_employees = db.query(func.count(AttendanceEmployee.id)).filter(
        AttendanceEmployee.tenant_id == tenant_id
    ).scalar() or 0
    active_employees = db.query(func.count(AttendanceEmployee.id)).filter(
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.is_active.is_(True),
    ).scalar() or 0
    present_employee_ids = db.query(distinct(DailyAttendanceRecord.employee_id)).join(
        AttendanceEmployee,
        AttendanceEmployee.id == DailyAttendanceRecord.employee_id,
    ).filter(
        DailyAttendanceRecord.tenant_id == tenant_id,
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.is_active.is_(True),
        DailyAttendanceRecord.attendance_date == tenant_date,
        DailyAttendanceRecord.status.in_(PRESENT_STATUSES),
    )
    today_present = present_employee_ids.count()
    today_late = db.query(func.count(distinct(DailyAttendanceRecord.employee_id))).join(
        AttendanceEmployee,
        AttendanceEmployee.id == DailyAttendanceRecord.employee_id,
    ).filter(
        DailyAttendanceRecord.tenant_id == tenant_id,
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.is_active.is_(True),
        DailyAttendanceRecord.attendance_date == tenant_date,
        DailyAttendanceRecord.status == "late",
    ).scalar() or 0

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "today_present": today_present,
        "today_absent": max(active_employees - today_present, 0),
        "today_late": today_late,
        "active_cameras": db.query(func.count(Camera.id)).filter(
            Camera.tenant_id == tenant_id,
            Camera.is_active.is_(True),
        ).scalar() or 0,
        "offline_cameras": db.query(func.count(Camera.id)).filter(
            Camera.tenant_id == tenant_id,
            Camera.is_active.is_(True),
            Camera.health_status.in_(OFFLINE_STATUSES),
        ).scalar() or 0,
        "unknown_face_alerts": db.query(func.count(Alert.id)).filter(
            Alert.tenant_id == tenant_id,
            Alert.alert_type == "UNKNOWN_FACE",
            Alert.status != "resolved",
        ).scalar() or 0,
    }


def get_recent_activity(db: Session, tenant_id: str, limit: int = 10) -> dict[str, list[dict]]:
    attendance_rows = (
        db.query(AttendanceEvent, AttendanceEmployee, Camera.name)
        .join(
            AttendanceEmployee,
            (AttendanceEmployee.id == AttendanceEvent.employee_id)
            & (AttendanceEmployee.tenant_id == tenant_id),
        )
        .outerjoin(
            Camera,
            (cast(Camera.id, String) == AttendanceEvent.camera_id) & (Camera.tenant_id == tenant_id),
        )
        .filter(AttendanceEvent.tenant_id == tenant_id)
        .order_by(AttendanceEvent.event_time.desc(), AttendanceEvent.id.desc())
        .limit(limit)
        .all()
    )
    recognition_rows = (
        db.query(CameraEvent, Camera.name, AttendanceEmployee.full_name)
        .join(
            Camera,
            (Camera.id == CameraEvent.camera_id) & (Camera.tenant_id == tenant_id),
        )
        .outerjoin(
            AttendanceEmployee,
            (AttendanceEmployee.id == CameraEvent.employee_id)
            & (AttendanceEmployee.tenant_id == tenant_id),
        )
        .filter(CameraEvent.tenant_id == tenant_id)
        .order_by(CameraEvent.created_at.desc(), CameraEvent.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "attendance_events": [
            {
                "id": event.id,
                "employee_id": employee.id,
                "employee_name": employee.full_name,
                "employee_code": employee.employee_code,
                "event_type": event.event_type,
                "source": event.source,
                "camera_id": event.camera_id,
                "camera_name": camera_name,
                "confidence": event.confidence,
                "event_time": event.event_time,
            }
            for event, employee, camera_name in attendance_rows
        ],
        "recognition_attempts": [
            {
                "id": event.id,
                "camera_id": event.camera_id,
                "camera_name": camera_name,
                "employee_id": event.employee_id,
                "employee_name": employee_name,
                "recognition_status": event.recognition_status,
                "confidence": event.confidence,
                "created_at": event.created_at,
            }
            for event, camera_name, employee_name in recognition_rows
        ],
    }

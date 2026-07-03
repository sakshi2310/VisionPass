"""Tenant-scoped access decision engine."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.access_event import AccessLog
from app.models.attendance import AttendanceHoliday, AttendanceSettings, AttendanceShift
from app.models.camera import Camera
from app.models.employee import AttendanceEmployee
from app.models.visitor import Visitor
from app.services.alert_service import create_alert

UNKNOWN_STATUSES = {"UNKNOWN", "NO_FACE", "MULTIPLE_FACES"}
DEFAULT_TIMEZONE = "Asia/Kolkata"


def _tenant_zone(db: Session, tenant_id: str) -> ZoneInfo:
    name = (
        db.query(AttendanceSettings.timezone)
        .filter(AttendanceSettings.tenant_id == tenant_id)
        .scalar()
        or DEFAULT_TIMEZONE
    )
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def _normalize_timestamp(value: datetime, zone: ZoneInfo) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=zone)
    return value.astimezone(zone)


def _employee_shift(db: Session, tenant_id: str, employee: AttendanceEmployee) -> AttendanceShift | None:
    if employee.shift_id:
        shift = (
            db.query(AttendanceShift)
            .filter(
                AttendanceShift.id == employee.shift_id,
                AttendanceShift.tenant_id == tenant_id,
                AttendanceShift.is_active.is_(True),
            )
            .one_or_none()
        )
        if shift is not None:
            return shift
    return (
        db.query(AttendanceShift)
        .filter(
            AttendanceShift.tenant_id == tenant_id,
            AttendanceShift.is_default.is_(True),
            AttendanceShift.is_active.is_(True),
        )
        .order_by(AttendanceShift.created_at.asc())
        .first()
    )


def _within_shift(timestamp: datetime, shift: AttendanceShift) -> bool:
    local_date = timestamp.date()
    start = datetime.combine(local_date, shift.start_time, timestamp.tzinfo)
    end = datetime.combine(local_date, shift.end_time, timestamp.tzinfo)
    if shift.end_time <= shift.start_time:
        if timestamp.timetz().replace(tzinfo=None) < shift.end_time:
            start -= timedelta(days=1)
        else:
            end += timedelta(days=1)
    grace = timedelta(minutes=settings.access_shift_grace_minutes)
    return start - grace <= timestamp <= end + grace


def _decision(
    db: Session,
    tenant_id: str,
    *,
    employee_id: str | None,
    visitor_id: str | None,
    confidence: float | None,
    recognition_status: str,
    timestamp: datetime,
) -> tuple[str, str, AttendanceEmployee | None, Visitor | None]:
    if recognition_status in UNKNOWN_STATUSES:
        return settings.access_unknown_face_action, "unknown_face", None, None
    if recognition_status == "LOW_CONFIDENCE" or confidence is None or confidence < settings.access_confidence_threshold:
        return "manual_review", "low_confidence", None, None

    employee = None
    visitor = None
    if employee_id:
        employee = (
            db.query(AttendanceEmployee)
            .filter(
                cast(AttendanceEmployee.id, String) == employee_id,
                AttendanceEmployee.tenant_id == tenant_id,
            )
            .one_or_none()
        )
        if employee is None:
            return "denied", "employee_not_found", None, None
        if not employee.is_active:
            return "denied", "inactive_employee", employee, None
    elif visitor_id:
        visitor = (
            db.query(Visitor)
            .filter(
                cast(Visitor.id, String) == visitor_id,
                Visitor.tenant_id == tenant_id,
            )
            .one_or_none()
        )
        if visitor is None:
            return "denied", "visitor_not_found", None, None
        if visitor.status == "blocked":
            return "denied", "blocked_visitor", None, visitor
        return "granted", "valid_visitor", None, visitor
    else:
        return settings.access_unknown_face_action, "identity_not_resolved", None, None

    zone = _tenant_zone(db, tenant_id)
    local_timestamp = _normalize_timestamp(timestamp, zone)
    holiday = (
        db.query(AttendanceHoliday.id)
        .filter(
            AttendanceHoliday.tenant_id == tenant_id,
            AttendanceHoliday.holiday_date == local_timestamp.date(),
            AttendanceHoliday.is_active.is_(True),
        )
        .first()
    )
    if holiday is not None:
        return settings.access_holiday_action, "holiday", employee, None

    shift = _employee_shift(db, tenant_id, employee)
    if shift is not None and not _within_shift(local_timestamp, shift):
        return settings.access_outside_shift_action, "outside_shift", employee, None
    return "granted", "active_employee_within_allowed_time", employee, None


def decide_access(
    db: Session,
    tenant_id: str,
    *,
    employee_id: str | None,
    visitor_id: str | None,
    camera_id: str | None,
    confidence: float | None,
    recognition_status: str,
    timestamp: datetime,
) -> AccessLog:
    camera = None
    if camera_id:
        camera = (
            db.query(Camera)
            .filter(cast(Camera.id, String) == camera_id, Camera.tenant_id == tenant_id)
            .one_or_none()
        )
        if camera is None:
            raise ValueError("Camera not found")

    decision, reason, employee, visitor = _decision(
        db,
        tenant_id,
        employee_id=employee_id,
        visitor_id=visitor_id,
        confidence=confidence,
        recognition_status=recognition_status,
        timestamp=timestamp,
    )
    log = AccessLog(
        tenant_id=tenant_id,
        employee_id=employee.id if employee else None,
        visitor_id=visitor.id if visitor else None,
        camera_id=camera.id if camera else None,
        decision=decision,
        reason=reason,
        confidence=confidence,
        created_at=_normalize_timestamp(timestamp, _tenant_zone(db, tenant_id)).astimezone(timezone.utc),
    )
    db.add(log)
    db.flush()
    if decision == "denied":
        alert_type = (
            "BLOCKED_VISITOR"
            if reason == "blocked_visitor"
            else "INACTIVE_EMPLOYEE_ATTEMPT"
            if reason == "inactive_employee"
            else "ACCESS_DENIED"
        )
        create_alert(
            db,
            tenant_id=tenant_id,
            alert_type=alert_type,
            message=f"Access was denied: {reason.replace('_', ' ')}.",
            source_type="access_log",
            source_id=log.id,
            metadata={
                "reason": reason,
                "employee_id": employee_id,
                "visitor_id": visitor_id,
                "camera_id": camera_id,
                "confidence": confidence,
            },
        )
    db.commit()
    db.refresh(log)
    return log


def list_access_logs(
    db: Session,
    tenant_id: str,
    *,
    decision: str | None = None,
    limit: int = 100,
) -> list[dict]:
    query = db.query(AccessLog).filter(AccessLog.tenant_id == tenant_id)
    if decision:
        query = query.filter(AccessLog.decision == decision)
    logs = query.order_by(AccessLog.created_at.desc()).limit(limit).all()
    employee_ids = {log.employee_id for log in logs if log.employee_id}
    visitor_ids = {log.visitor_id for log in logs if log.visitor_id}
    camera_ids = {log.camera_id for log in logs if log.camera_id}
    employee_names = dict(
        db.query(AttendanceEmployee.id, AttendanceEmployee.full_name)
        .filter(AttendanceEmployee.tenant_id == tenant_id, AttendanceEmployee.id.in_(employee_ids))
        .all()
    ) if employee_ids else {}
    visitor_names = dict(
        db.query(Visitor.id, Visitor.full_name)
        .filter(Visitor.tenant_id == tenant_id, Visitor.id.in_(visitor_ids))
        .all()
    ) if visitor_ids else {}
    camera_names = dict(
        db.query(Camera.id, Camera.name)
        .filter(Camera.tenant_id == tenant_id, Camera.id.in_(camera_ids))
        .all()
    ) if camera_ids else {}
    return [
        {
            "log": log,
            "identity_name": employee_names.get(log.employee_id) or visitor_names.get(log.visitor_id),
            "camera_name": camera_names.get(log.camera_id),
        }
        for log in logs
    ]

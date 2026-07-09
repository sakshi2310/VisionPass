"""Attendance service helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
import logging
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models.attendance import (
    AttendanceEvent,
    AttendanceHoliday,
    AttendancePresenceSession,
    AttendanceSettings,
    AttendanceShift,
    AttendanceWorkingDay,
    DailyAttendanceRecord,
)
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee
from app.services.alert_service import create_alert

DEFAULT_TIMEZONE = "Asia/Kolkata"
DEFAULT_WORKING_DAY_MAP = {
    0: False,
    1: True,
    2: True,
    3: True,
    4: True,
    5: True,
    6: True,
}

logger = logging.getLogger(__name__)


class AttendanceMarkError(ValueError):
    """A user-correctable attendance state transition was rejected."""

    def __init__(self, code: str, message: str, *, status_code: int = 409) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def _parse_time(value: str | time | None, *, field_name: str, required: bool = False) -> time | None:
    if value is None:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    if isinstance(value, time):
        return value
    normalized = value.strip()
    if not normalized:
        if required:
            raise ValueError(f"{field_name} is required")
        return None
    for format_string in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(normalized, format_string).time()
        except ValueError:
            continue
    raise ValueError(f"{field_name} must be a valid time in HH:MM format")


def _ensure_settings_seeded(db: Session, tenant_id: str) -> AttendanceSettings:
    settings = db.query(AttendanceSettings).filter(AttendanceSettings.tenant_id == tenant_id).one_or_none()
    if settings is None:
        settings = AttendanceSettings(
            tenant_id=tenant_id,
            duplicate_detection_cooldown_minutes=app_settings.attendance_duplicate_cooldown_minutes,
            allow_manual_correction=True,
            require_correction_reason=True,
            timezone=DEFAULT_TIMEZONE,
        )
        db.add(settings)
        db.flush()

    existing_days = {
        row.day_of_week: row
        for row in db.query(AttendanceWorkingDay).filter(AttendanceWorkingDay.tenant_id == tenant_id).all()
    }
    for day_of_week, is_working in DEFAULT_WORKING_DAY_MAP.items():
        row = existing_days.get(day_of_week)
        if row is None:
            db.add(
                AttendanceWorkingDay(
                    tenant_id=tenant_id,
                    day_of_week=day_of_week,
                    is_working=is_working,
                )
            )
        elif settings is None and row.is_working is None:
            row.is_working = is_working

    db.commit()
    db.refresh(settings)
    return settings


def get_attendance_settings_bundle(db: Session, tenant_id: str) -> dict:
    settings = _ensure_settings_seeded(db, tenant_id)
    working_days = (
        db.query(AttendanceWorkingDay)
        .filter(AttendanceWorkingDay.tenant_id == tenant_id)
        .order_by(AttendanceWorkingDay.day_of_week.asc())
        .all()
    )
    return {"attendance_settings": settings, "working_days": working_days}


def update_attendance_settings(
    db: Session,
    tenant_id: str,
    *,
    duplicate_detection_cooldown_minutes: int,
    allow_manual_correction: bool,
    require_correction_reason: bool,
    timezone: str,
    working_days: Iterable[int],
) -> dict:
    normalized_working_days = sorted({int(day) for day in working_days})
    if not normalized_working_days:
        raise ValueError("At least one working day should be selected")
    if duplicate_detection_cooldown_minutes < 1:
        raise ValueError("Cooldown must be at least 1 minute")
    if not timezone.strip():
        raise ValueError("Timezone is required")
    if any(day < 0 or day > 6 for day in normalized_working_days):
        raise ValueError("Working days must be between 0 and 6")

    settings = db.query(AttendanceSettings).filter(AttendanceSettings.tenant_id == tenant_id).one_or_none()
    if settings is None:
        settings = AttendanceSettings(tenant_id=tenant_id)
        db.add(settings)
        db.flush()

    settings.duplicate_detection_cooldown_minutes = duplicate_detection_cooldown_minutes
    settings.allow_manual_correction = allow_manual_correction
    settings.require_correction_reason = require_correction_reason
    settings.timezone = timezone.strip()

    existing_days = {
        row.day_of_week: row
        for row in db.query(AttendanceWorkingDay).filter(AttendanceWorkingDay.tenant_id == tenant_id).all()
    }
    for day_of_week in range(7):
        row = existing_days.get(day_of_week)
        should_work = day_of_week in normalized_working_days
        if row is None:
            db.add(
                AttendanceWorkingDay(
                    tenant_id=tenant_id,
                    day_of_week=day_of_week,
                    is_working=should_work,
                )
            )
        else:
            row.is_working = should_work

    db.commit()
    db.refresh(settings)
    return get_attendance_settings_bundle(db, tenant_id)


def list_shifts(db: Session, tenant_id: str) -> list[AttendanceShift]:
    return (
        db.query(AttendanceShift)
        .filter(AttendanceShift.tenant_id == tenant_id)
        .order_by(AttendanceShift.is_default.desc(), AttendanceShift.is_active.desc(), AttendanceShift.name.asc())
        .all()
    )


def get_shift(db: Session, tenant_id: str, shift_id: str) -> AttendanceShift | None:
    return (
        db.query(AttendanceShift)
        .filter(AttendanceShift.tenant_id == tenant_id, AttendanceShift.id == shift_id)
        .one_or_none()
    )


def create_shift(
    db: Session,
    tenant_id: str,
    *,
    name: str,
    start_time: str | time,
    end_time: str | time,
    grace_period_minutes: int = app_settings.attendance_late_grace_minutes,
    late_after_minutes: int = app_settings.attendance_late_grace_minutes,
    half_day_min_minutes: int,
    full_day_min_minutes: int,
    auto_checkout_time: str | time | None = None,
    break_duration_minutes: int = 0,
    is_default: bool = False,
    is_active: bool = True,
) -> AttendanceShift:
    normalized_name = name.strip()
    if not normalized_name:
        raise ValueError("Shift name is required")
    if full_day_min_minutes <= half_day_min_minutes:
        raise ValueError("Full day minimum minutes must be greater than half day minimum minutes")

    shift = AttendanceShift(
        tenant_id=tenant_id,
        name=normalized_name,
        start_time=_parse_time(start_time, field_name="start_time", required=True),
        end_time=_parse_time(end_time, field_name="end_time", required=True),
        grace_period_minutes=grace_period_minutes,
        late_after_minutes=late_after_minutes,
        half_day_min_minutes=half_day_min_minutes,
        full_day_min_minutes=full_day_min_minutes,
        auto_checkout_time=_parse_time(auto_checkout_time, field_name="auto_checkout_time"),
        break_duration_minutes=break_duration_minutes,
        is_default=is_default,
        is_active=is_active,
    )
    db.add(shift)
    db.flush()
    if is_default:
        _unset_other_defaults(db, tenant_id, shift.id)
    db.commit()
    db.refresh(shift)
    return shift


def update_shift(
    db: Session,
    tenant_id: str,
    shift_id: str,
    *,
    name: str | None = None,
    start_time: str | time | None = None,
    end_time: str | time | None = None,
    grace_period_minutes: int | None = None,
    late_after_minutes: int | None = None,
    half_day_min_minutes: int | None = None,
    full_day_min_minutes: int | None = None,
    auto_checkout_time: str | time | None = None,
    break_duration_minutes: int | None = None,
    is_default: bool | None = None,
    is_active: bool | None = None,
) -> AttendanceShift | None:
    shift = get_shift(db, tenant_id, shift_id)
    if shift is None:
        return None

    if name is not None:
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Shift name is required")
        shift.name = normalized_name
    if start_time is not None:
        shift.start_time = _parse_time(start_time, field_name="start_time", required=True)
    if end_time is not None:
        shift.end_time = _parse_time(end_time, field_name="end_time", required=True)
    if grace_period_minutes is not None:
        if grace_period_minutes < 0:
            raise ValueError("Grace period cannot be negative")
        shift.grace_period_minutes = grace_period_minutes
    if late_after_minutes is not None:
        if late_after_minutes < 0:
            raise ValueError("Late after minutes cannot be negative")
        shift.late_after_minutes = late_after_minutes
    if half_day_min_minutes is not None:
        shift.half_day_min_minutes = half_day_min_minutes
    if full_day_min_minutes is not None:
        shift.full_day_min_minutes = full_day_min_minutes
    if shift.full_day_min_minutes <= shift.half_day_min_minutes:
        raise ValueError("Full day minimum minutes must be greater than half day minimum minutes")
    if auto_checkout_time is not None:
        shift.auto_checkout_time = _parse_time(auto_checkout_time, field_name="auto_checkout_time")
    if break_duration_minutes is not None:
        if break_duration_minutes < 0:
            raise ValueError("Break duration cannot be negative")
        shift.break_duration_minutes = break_duration_minutes
    if is_default is not None:
        shift.is_default = is_default
    if is_active is not None:
        shift.is_active = is_active

    db.add(shift)
    db.flush()
    if shift.is_default:
        _unset_other_defaults(db, tenant_id, shift.id)
    db.commit()
    db.refresh(shift)
    return shift


def delete_shift(db: Session, tenant_id: str, shift_id: str) -> bool:
    shift = get_shift(db, tenant_id, shift_id)
    if shift is None:
        return False
    db.delete(shift)
    db.commit()
    return True


def set_default_shift(db: Session, tenant_id: str, shift_id: str) -> AttendanceShift | None:
    shift = get_shift(db, tenant_id, shift_id)
    if shift is None:
        return None
    _unset_other_defaults(db, tenant_id, shift.id)
    shift.is_default = True
    db.add(shift)
    db.commit()
    db.refresh(shift)
    return shift


def _unset_other_defaults(db: Session, tenant_id: str, shift_id: str) -> None:
    db.query(AttendanceShift).filter(
        AttendanceShift.tenant_id == tenant_id,
        AttendanceShift.id != shift_id,
        AttendanceShift.is_default.is_(True),
    ).update({AttendanceShift.is_default: False}, synchronize_session=False)


def list_holidays(db: Session, tenant_id: str) -> list[AttendanceHoliday]:
    holidays = (
        db.query(AttendanceHoliday)
        .filter(AttendanceHoliday.tenant_id == tenant_id)
        .order_by(AttendanceHoliday.holiday_date.asc(), AttendanceHoliday.holiday_name.asc())
        .all()
    )
    today = date.today()
    return sorted(holidays, key=lambda item: (item.holiday_date < today, item.holiday_date, item.holiday_name.lower()))


def get_holiday(db: Session, tenant_id: str, holiday_id: str) -> AttendanceHoliday | None:
    return (
        db.query(AttendanceHoliday)
        .filter(AttendanceHoliday.tenant_id == tenant_id, AttendanceHoliday.id == holiday_id)
        .one_or_none()
    )


def _ensure_holiday_date_unique(
    db: Session,
    tenant_id: str,
    holiday_date: date,
    *,
    exclude_id: str | None = None,
) -> None:
    query = db.query(AttendanceHoliday).filter(
        AttendanceHoliday.tenant_id == tenant_id,
        AttendanceHoliday.holiday_date == holiday_date,
    )
    if exclude_id is not None:
        query = query.filter(AttendanceHoliday.id != exclude_id)
    if query.first() is not None:
        raise ValueError("Duplicate holiday date is not allowed for this tenant")


def create_holiday(
    db: Session,
    tenant_id: str,
    *,
    holiday_name: str,
    holiday_date: date,
    department_id: str | None = None,
    location_id: str | None = None,
    is_active: bool = True,
) -> AttendanceHoliday:
    normalized_name = holiday_name.strip()
    if not normalized_name:
        raise ValueError("Holiday name is required")
    _ensure_holiday_date_unique(db, tenant_id, holiday_date)

    holiday = AttendanceHoliday(
        tenant_id=tenant_id,
        holiday_name=normalized_name,
        holiday_date=holiday_date,
        department_id=department_id or None,
        location_id=location_id or None,
        is_active=is_active,
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


def update_holiday(
    db: Session,
    tenant_id: str,
    holiday_id: str,
    *,
    holiday_name: str | None = None,
    holiday_date: date | None = None,
    department_id: str | None = None,
    location_id: str | None = None,
    is_active: bool | None = None,
) -> AttendanceHoliday | None:
    holiday = get_holiday(db, tenant_id, holiday_id)
    if holiday is None:
        return None
    if holiday_name is not None:
        normalized_name = holiday_name.strip()
        if not normalized_name:
            raise ValueError("Holiday name is required")
        holiday.holiday_name = normalized_name
    if holiday_date is not None:
        _ensure_holiday_date_unique(db, tenant_id, holiday_date, exclude_id=holiday_id)
        holiday.holiday_date = holiday_date
    if department_id is not None:
        holiday.department_id = department_id or None
    if location_id is not None:
        holiday.location_id = location_id or None
    if is_active is not None:
        holiday.is_active = is_active

    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return holiday


def delete_holiday(db: Session, tenant_id: str, holiday_id: str) -> bool:
    holiday = get_holiday(db, tenant_id, holiday_id)
    if holiday is None:
        return False
    db.delete(holiday)
    db.commit()
    return True


def _tenant_zone(db: Session, tenant_id: str) -> ZoneInfo:
    attendance_settings = _ensure_settings_seeded(db, tenant_id)
    try:
        return ZoneInfo(attendance_settings.timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def _normalize_event_time(value: datetime | None, tenant_zone: ZoneInfo) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=tenant_zone)
    return value.astimezone(timezone.utc)


def _employee_shift(db: Session, tenant_id: str, employee: AttendanceEmployee) -> AttendanceShift | None:
    if employee.shift_id:
        assigned = (
            db.query(AttendanceShift)
            .filter(
                AttendanceShift.tenant_id == tenant_id,
                AttendanceShift.id == employee.shift_id,
                AttendanceShift.is_active.is_(True),
            )
            .one_or_none()
        )
        if assigned is not None:
            return assigned
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


def _is_holiday(db: Session, tenant_id: str, attendance_date: date) -> bool:
    return (
        db.query(AttendanceHoliday.id)
        .filter(
            AttendanceHoliday.tenant_id == tenant_id,
            AttendanceHoliday.holiday_date == attendance_date,
            AttendanceHoliday.is_active.is_(True),
        )
        .first()
        is not None
    )


def _is_working_day(db: Session, tenant_id: str, attendance_date: date) -> bool:
    row = (
        db.query(AttendanceWorkingDay.is_working)
        .filter(
            AttendanceWorkingDay.tenant_id == tenant_id,
            AttendanceWorkingDay.day_of_week == attendance_date.weekday(),
        )
        .one_or_none()
    )
    if row is None:
        return DEFAULT_WORKING_DAY_MAP.get(attendance_date.weekday(), True)
    return bool(row[0])


def _daily_record(
    db: Session,
    tenant_id: str,
    employee_id: str,
    attendance_date: date,
    *,
    lock: bool = False,
) -> DailyAttendanceRecord | None:
    query = db.query(DailyAttendanceRecord).filter(
        DailyAttendanceRecord.tenant_id == tenant_id,
        DailyAttendanceRecord.employee_id == employee_id,
        DailyAttendanceRecord.attendance_date == attendance_date,
    )
    if lock:
        query = query.with_for_update()
    return query.one_or_none()


def _latest_event(
    db: Session,
    tenant_id: str,
    employee_id: str,
    event_type: str,
) -> AttendanceEvent | None:
    return (
        db.query(AttendanceEvent)
        .filter(
            AttendanceEvent.tenant_id == tenant_id,
            AttendanceEvent.employee_id == employee_id,
            AttendanceEvent.event_type == event_type,
        )
        .order_by(AttendanceEvent.event_time.desc())
        .first()
    )


def _ensure_not_duplicate(
    db: Session,
    tenant_id: str,
    employee_id: str,
    event_type: str,
    event_time: datetime,
) -> None:
    previous = _latest_event(db, tenant_id, employee_id, event_type)
    if previous is None:
        return
    elapsed = event_time - previous.event_time
    if elapsed.total_seconds() < 0:
        raise AttendanceMarkError("INVALID_EVENT_TIME", "Attendance time cannot precede the latest event.")
    cooldown = timedelta(minutes=app_settings.attendance_duplicate_cooldown_minutes)
    if elapsed < cooldown:
        label = "check-in" if event_type == "check_in" else "check-out"
        create_alert(
            db,
            tenant_id=tenant_id,
            alert_type="DUPLICATE_ATTENDANCE_ATTEMPT",
            message=f"Duplicate {label} attempt was blocked.",
            source_type="attendance_employee",
            source_id=employee_id,
            metadata={
                "event_type": event_type,
                "elapsed_seconds": elapsed.total_seconds(),
                "cooldown_minutes": app_settings.attendance_duplicate_cooldown_minutes,
            },
        )
        db.commit()
        raise AttendanceMarkError(
            f"DUPLICATE_{event_type.upper()}",
            (
                f"Duplicate {label} blocked. Try again after "
                f"{app_settings.attendance_duplicate_cooldown_minutes} minutes."
            ),
        )


def log_live_recognition_decision(
    *,
    camera_enabled: bool,
    tenant_id: str,
    camera_id: str | None,
    frame_received: bool,
    face_detected: bool,
    matched: bool,
    employee_id: str | None,
    employee_name: str | None,
    confidence: float | None,
    decided_event: str,
    final_status: str,
    reason: str | None = None,
) -> None:
    logger.info(
        (
            "[LIVE_RECOGNITION] tenant_id=%s camera_id=%s camera_enabled=%s frame_received=%s "
            "face_detected=%s matched=%s employee_id=%s employee_name=%s confidence=%s "
            "decided_event=%s final_status=%s reason=%s"
        ),
        tenant_id,
        camera_id,
        camera_enabled,
        frame_received,
        face_detected,
        matched,
        employee_id,
        employee_name,
        confidence,
        decided_event,
        final_status,
        reason or "-",
    )


def process_camera_presence_recognition(
    db: Session,
    tenant_id: str,
    *,
    employee_id: str | None,
    employee_name: str | None,
    confidence: float | None,
    recognition_status: str,
    camera_id: str | None = None,
    camera_enabled: bool = True,
    event_time: datetime | None = None,
) -> dict:
    tenant_zone = _tenant_zone(db, tenant_id)
    occurred_at = _normalize_event_time(event_time, tenant_zone)
    attendance_date = occurred_at.astimezone(tenant_zone).date()

    if employee_id is None:
        reason = "Unknown face detected" if recognition_status == "UNKNOWN" else "No face detected" if recognition_status == "NO_FACE" else "Face was not matched"
        final_status = "not_detected"
        log_live_recognition_decision(
            camera_enabled=camera_enabled,
            tenant_id=tenant_id,
            camera_id=camera_id,
            frame_received=True,
            face_detected=False,
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=confidence,
            decided_event="no_face" if recognition_status == "NO_FACE" else "unknown_face" if recognition_status == "UNKNOWN" else "error",
            final_status=final_status,
            reason=reason,
        )
        return {
            "attendance": None,
            "decision": "no_face" if recognition_status == "NO_FACE" else "unknown_face" if recognition_status == "UNKNOWN" else "error",
            "final_attendance_status": final_status,
            "reason": reason,
        }

    employee = (
        db.query(AttendanceEmployee)
        .filter(
            AttendanceEmployee.tenant_id == tenant_id,
            AttendanceEmployee.id == employee_id,
            AttendanceEmployee.is_active.is_(True),
        )
        .one_or_none()
    )
    if employee is None:
        reason = "Employee not found or inactive"
        log_live_recognition_decision(
            camera_enabled=camera_enabled,
            tenant_id=tenant_id,
            camera_id=camera_id,
            frame_received=True,
            face_detected=True,
            matched=False,
            employee_id=employee_id,
            employee_name=employee_name,
            confidence=confidence,
            decided_event="error",
            final_status="not_detected",
            reason=reason,
        )
        return {
            "attendance": None,
            "decision": "error",
            "final_attendance_status": "not_detected",
            "reason": reason,
        }

    daily = _daily_record(db, tenant_id, employee_id, attendance_date, lock=True)
    shift = _employee_shift(db, tenant_id, employee)
    if daily is not None and daily.first_check_in is not None:
        final_status = daily.status or "present"
        reason = "Employee already has a check-in today"
        log_live_recognition_decision(
            camera_enabled=camera_enabled,
            tenant_id=tenant_id,
            camera_id=camera_id,
            frame_received=True,
            face_detected=True,
            matched=True,
            employee_id=employee_id,
            employee_name=employee.full_name,
            confidence=confidence,
            decided_event="duplicate",
            final_status=final_status,
            reason=reason,
        )
        return {
            "attendance": None,
            "decision": "duplicate",
            "final_attendance_status": final_status,
            "reason": reason,
        }

    try:
        result = mark_attendance(
            db,
            tenant_id,
            employee_id,
            event_type="check_in",
            source="camera",
            camera_id=camera_id,
            confidence=confidence,
            event_time=occurred_at,
            metadata={
                "recognition_status": recognition_status,
                "presence_mode": "camera",
                "camera_enabled": camera_enabled,
                "decision": "check_in",
            },
        )
    except AttendanceMarkError as exc:
        log_live_recognition_decision(
            camera_enabled=camera_enabled,
            tenant_id=tenant_id,
            camera_id=camera_id,
            frame_received=True,
            face_detected=True,
            matched=True,
            employee_id=employee_id,
            employee_name=employee.full_name,
            confidence=confidence,
            decided_event="error",
            final_status="not_detected",
            reason=exc.message,
        )
        raise

    final_status = result["daily"].status
    reason = "Check-in recorded from live camera"
    if final_status == "late":
        reason = "Check-in recorded after shift cutoff"
    log_live_recognition_decision(
        camera_enabled=camera_enabled,
        tenant_id=tenant_id,
        camera_id=camera_id,
        frame_received=True,
        face_detected=True,
        matched=True,
        employee_id=employee_id,
        employee_name=employee.full_name,
        confidence=confidence,
        decided_event="check_in",
        final_status=final_status,
        reason=reason,
    )
    return {
        "attendance": result,
        "decision": "check_in",
        "final_attendance_status": final_status,
        "reason": reason,
    }


def _initial_status(
    db: Session,
    tenant_id: str,
    attendance_date: date,
    event_time: datetime,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
) -> str:
    if _is_holiday(db, tenant_id, attendance_date):
        return "holiday"
    if shift is None:
        return "present"
    local_event = event_time.astimezone(tenant_zone)
    shift_start = datetime.combine(attendance_date, shift.start_time, tzinfo=tenant_zone)
    late_after = shift_start + timedelta(minutes=app_settings.attendance_late_grace_minutes)
    return "late" if local_event > late_after else "present"


def mark_attendance(
    db: Session,
    tenant_id: str,
    employee_id: str,
    *,
    event_type: str,
    source: str,
    camera_id: str | None = None,
    confidence: float | None = None,
    event_time: datetime | None = None,
    metadata: dict | None = None,
) -> dict:
    """Create an event and update the employee's tenant-local daily record."""

    employee = (
        db.query(AttendanceEmployee)
        .filter(
            AttendanceEmployee.tenant_id == tenant_id,
            AttendanceEmployee.id == employee_id,
            AttendanceEmployee.is_active.is_(True),
        )
        .one_or_none()
    )
    if employee is None:
        raise AttendanceMarkError("EMPLOYEE_NOT_FOUND", "Employee not found.", status_code=404)
    if event_type not in {"check_in", "check_out"}:
        raise AttendanceMarkError("INVALID_EVENT_TYPE", "Event type must be check_in or check_out.", status_code=422)
    if source not in {"camera", "manual", "web"}:
        raise AttendanceMarkError("INVALID_SOURCE", "Source must be camera, manual, or web.", status_code=422)

    tenant_zone = _tenant_zone(db, tenant_id)
    occurred_at = _normalize_event_time(event_time, tenant_zone)
    attendance_date = occurred_at.astimezone(tenant_zone).date()
    _ensure_not_duplicate(db, tenant_id, employee_id, event_type, occurred_at)
    daily = _daily_record(db, tenant_id, employee_id, attendance_date, lock=True)
    shift = _employee_shift(db, tenant_id, employee)

    if event_type == "check_in":
        if daily is not None and daily.last_check_out is not None:
            raise AttendanceMarkError(
                "ALREADY_CHECKED_OUT",
                "Attendance for this employee is already checked out for today.",
            )
        if daily is not None and daily.first_check_in is not None:
            raise AttendanceMarkError("ALREADY_CHECKED_IN", "Employee is already checked in.")
        if daily is None:
            daily = DailyAttendanceRecord(
                tenant_id=tenant_id,
                employee_id=employee_id,
                attendance_date=attendance_date,
                shift_id=shift.id if shift else None,
            )
            db.add(daily)
        daily.first_check_in = occurred_at
        daily.status = _initial_status(
            db,
            tenant_id,
            attendance_date,
            occurred_at,
            tenant_zone,
            shift,
        )
        message = "Check-in recorded."
    else:
        if daily is None or daily.first_check_in is None:
            raise AttendanceMarkError(
                "CHECK_IN_REQUIRED",
                "Employee must check in before checking out.",
            )
        if daily.last_check_out is not None:
            raise AttendanceMarkError("ALREADY_CHECKED_OUT", "Employee is already checked out.")
        if occurred_at <= daily.first_check_in:
            raise AttendanceMarkError(
                "CHECK_OUT_BEFORE_CHECK_IN",
                "Check-out time must be after check-in time.",
            )
        daily.last_check_out = occurred_at
        elapsed_minutes = int((occurred_at - daily.first_check_in).total_seconds() // 60)
        break_minutes = shift.break_duration_minutes if shift else 0
        daily.total_work_minutes = max(0, elapsed_minutes - break_minutes)
        if daily.status != "holiday" and shift and daily.total_work_minutes < shift.half_day_min_minutes:
            daily.status = "half_day"
        message = "Check-out recorded."

    event = AttendanceEvent(
        tenant_id=tenant_id,
        employee_id=employee_id,
        event_type=event_type,
        source=source,
        camera_id=camera_id,
        confidence=confidence,
        event_time=occurred_at,
        event_metadata=metadata or {},
    )
    db.add(event)
    db.add(daily)
    db.commit()
    db.refresh(event)
    db.refresh(daily)
    logger.info(
        (
            "[ATTENDANCE_EVENT] tenant_id=%s employee_id=%s employee_name=%s event_type=%s "
            "source=%s event_time=%s daily_record_id=%s final_day_status=%s"
        ),
        tenant_id,
        employee_id,
        employee.full_name,
        event_type,
        source,
        event.event_time.isoformat(),
        daily.id,
        daily.status,
    )
    return {
        "event": event,
        "daily": daily,
        "employee": employee,
        "message": message,
    }


def determine_next_attendance_event(
    db: Session,
    tenant_id: str,
    employee_id: str,
    *,
    event_time: datetime | None = None,
) -> str:
    tenant_zone = _tenant_zone(db, tenant_id)
    occurred_at = _normalize_event_time(event_time, tenant_zone)
    attendance_date = occurred_at.astimezone(tenant_zone).date()
    daily = _daily_record(db, tenant_id, employee_id, attendance_date)
    if daily is None or daily.first_check_in is None:
        return "check_in"
    if daily.last_check_out is not None:
        raise AttendanceMarkError("ALREADY_CHECKED_OUT", "Employee is already checked out for today.")
    since_check_in = occurred_at - daily.first_check_in
    cooldown = timedelta(minutes=app_settings.attendance_duplicate_cooldown_minutes)
    if since_check_in < cooldown:
        create_alert(
            db,
            tenant_id=tenant_id,
            alert_type="DUPLICATE_ATTENDANCE_ATTEMPT",
            message="A duplicate attendance attempt was blocked.",
            source_type="attendance_employee",
            source_id=employee_id,
            metadata={
                "elapsed_seconds": since_check_in.total_seconds(),
                "cooldown_minutes": app_settings.attendance_duplicate_cooldown_minutes,
            },
        )
        db.commit()
        raise AttendanceMarkError(
            "DUPLICATE_ATTENDANCE_ATTEMPT",
            (
                "Attendance was just recorded. Try again after "
                f"{app_settings.attendance_duplicate_cooldown_minutes} minutes."
            ),
        )
    return "check_out"


def list_today_attendance(
    db: Session,
    tenant_id: str,
    *,
    employee_id: str | None = None,
    current_time: datetime | None = None,
) -> list[dict]:
    tenant_zone = _tenant_zone(db, tenant_id)
    today = _normalize_event_time(current_time, tenant_zone).astimezone(tenant_zone).date()
    query = (
        db.query(DailyAttendanceRecord, AttendanceEmployee)
        .join(
            AttendanceEmployee,
            (AttendanceEmployee.id == DailyAttendanceRecord.employee_id)
            & (AttendanceEmployee.tenant_id == DailyAttendanceRecord.tenant_id),
        )
        .filter(
            DailyAttendanceRecord.tenant_id == tenant_id,
            DailyAttendanceRecord.attendance_date == today,
        )
        .order_by(DailyAttendanceRecord.first_check_in.desc())
    )
    if employee_id is not None:
        query = query.filter(DailyAttendanceRecord.employee_id == employee_id)
    rows = query.all()
    return [
        {
            "record": record,
            "employee_name": employee.full_name,
            "employee_code": employee.employee_code,
        }
        for record, employee in rows
    ]



def _parse_attendance_board_date(value: date | str | None, tenant_zone: ZoneInfo) -> date:
    if value is None:
        return datetime.now(timezone.utc).astimezone(tenant_zone).date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _combine_local_datetime(attendance_date: date, value: time | None, tenant_zone: ZoneInfo) -> datetime | None:
    if value is None:
        return None
    return datetime.combine(attendance_date, value, tzinfo=tenant_zone)


def _selected_day_bounds(attendance_date: date, tenant_zone: ZoneInfo) -> tuple[datetime, datetime]:
    start_local = datetime.combine(attendance_date, time.min, tzinfo=tenant_zone)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)


def _board_status_reason(
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
    now_utc: datetime,
    is_holiday: bool,
    is_working_day: bool,
) -> str:
    today_local = now_utc.astimezone(tenant_zone).date()
    if is_holiday:
        return "Holiday"
    if not is_working_day:
        return "Non-working day"
    if attendance_date < today_local:
        return "Absent on selected date"
    if attendance_date > today_local:
        return "Future date"
    if shift is None:
        return "No shift assigned"
    cutoff_local = _combine_local_datetime(attendance_date, shift.start_time, tenant_zone)
    if cutoff_local is None:
        return "No shift cutoff configured"
    cutoff_local = cutoff_local + timedelta(minutes=shift.late_after_minutes or shift.grace_period_minutes or 0)
    if now_utc.astimezone(tenant_zone) > cutoff_local:
        return "Absent after cutoff"
    return "No camera detection yet"


def _status_for_board(
    record: DailyAttendanceRecord | None,
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
    now_utc: datetime,
    is_holiday: bool,
    is_working_day: bool,
) -> str:
    if record is not None:
        return record.status
    if is_holiday or not is_working_day:
        return "holiday"
    today_local = now_utc.astimezone(tenant_zone).date()
    if attendance_date < today_local:
        return "absent"
    if attendance_date > today_local:
        return "not_detected"
    if shift is None:
        return "not_detected"
    cutoff_local = _combine_local_datetime(attendance_date, shift.start_time, tenant_zone)
    if cutoff_local is None:
        return "not_detected"
    cutoff_local = cutoff_local + timedelta(minutes=shift.late_after_minutes or shift.grace_period_minutes or 0)
    return "absent" if now_utc.astimezone(tenant_zone) > cutoff_local else "not_detected"


def _daily_present_minutes(
    record: DailyAttendanceRecord | None,
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    now_utc: datetime,
) -> int:
    if record is None or record.first_check_in is None:
        return 0
    if record.last_check_out is not None:
        if record.total_work_minutes:
            return int(record.total_work_minutes)
        return max(0, int((record.last_check_out - record.first_check_in).total_seconds() // 60))
    if attendance_date == now_utc.astimezone(tenant_zone).date():
        return max(0, int((now_utc - record.first_check_in).total_seconds() // 60))
    return int(record.total_work_minutes or 0)


def _board_cutoff_local(
    *,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
) -> datetime | None:
    if shift is None:
        return None
    cutoff_local = _combine_local_datetime(attendance_date, shift.start_time, tenant_zone)
    if cutoff_local is None:
        return None
    return cutoff_local + timedelta(minutes=shift.late_after_minutes or shift.grace_period_minutes or 0)


def _board_employee_reason(
    *,
    status: str,
    attendance_date: date,
    tenant_zone: ZoneInfo,
    shift: AttendanceShift | None,
    now_utc: datetime,
    is_holiday: bool,
    is_working_day: bool,
    latest_event: AttendanceEvent | None,
) -> str:
    today_local = now_utc.astimezone(tenant_zone).date()
    if is_holiday:
        return "Holiday"
    if not is_working_day:
        return "Non-working day"
    if status == "present":
        return "Visible in live camera feed."
    if status == "absent":
        return "Absent after attendance cutoff."
    if status == "not_detected":
        cutoff_local = _board_cutoff_local(attendance_date=attendance_date, tenant_zone=tenant_zone, shift=shift)
        if attendance_date == today_local and cutoff_local is not None and now_utc.astimezone(tenant_zone) <= cutoff_local:
            return "Not detected yet."
        return "No camera detection/check-in found."
    return "No camera detection/check-in found."


def _build_board_employee_row(
    *,
    employee: AttendanceEmployee,
    record: DailyAttendanceRecord | None,
    latest_event: AttendanceEvent | None,
    status: str,
    reason: str,
    work_minutes: int,
    sessions: list[dict],
) -> dict:
    latest_event_time = getattr(latest_event, "event_time", None) or getattr(latest_event, "created_at", None)
    check_in_time = record.first_check_in if record and record.first_check_in else (sessions[0]["check_in"] if sessions else None)
    check_out_time = record.last_check_out if record and record.last_check_out else (
        sessions[-1]["check_out"] if sessions and sessions[-1]["check_out"] is not None else None
    )
    last_seen_time = record.last_check_out if record and record.last_check_out else latest_event_time
    return {
        "employee_id": employee.id,
        "employee_code": employee.employee_code,
        "employee_name": employee.full_name,
        "email": employee.email,
        "department": employee.department,
        "designation": employee.designation,
        "shift_id": employee.shift_id,
        "status": status,
        "check_in_time": check_in_time,
        "check_out_time": check_out_time,
        "work_minutes": work_minutes,
        "latest_source": getattr(latest_event, "source", None),
        "latest_event_time": latest_event_time,
        "latest_event_type": getattr(latest_event, "event_type", None),
        "last_seen_time": last_seen_time,
        "reason": reason,
        "camera_id": getattr(latest_event, "camera_id", None),
        "sessions_count": len(sessions),
    }


def _build_latest_session_rows(
    *,
    db: Session,
    tenant_id: str,
    selected_date: date,
    start_utc: datetime,
    end_utc: datetime,
    camera_names: dict[str, str],
) -> list[dict]:
    rows = (
        db.query(AttendanceEvent, AttendanceEmployee)
        .join(
            AttendanceEmployee,
            (AttendanceEmployee.id == AttendanceEvent.employee_id)
            & (AttendanceEmployee.tenant_id == AttendanceEvent.tenant_id),
        )
        .filter(
            AttendanceEvent.tenant_id == tenant_id,
            AttendanceEvent.event_time >= start_utc,
            AttendanceEvent.event_time < end_utc,
        )
        .order_by(AttendanceEvent.event_time.desc())
        .all()
    )
    latest_sessions: list[dict] = []
    for event, employee in rows:
        latest_sessions.append(
            {
                "event_id": event.id,
                "employee_id": employee.id,
                "employee_code": employee.employee_code,
                "employee_name": employee.full_name,
                "event_type": event.event_type,
                "source": event.source,
                "event_time": event.event_time,
                "camera_id": event.camera_id,
                "camera_name": camera_names.get(event.camera_id) if event.camera_id else None,
                "confidence": float(event.confidence) if event.confidence is not None else None,
                "metadata": event.event_metadata or {},
            }
        )
    return latest_sessions


def _latest_presence_session(
    db: Session,
    tenant_id: str,
    employee_id: str,
    attendance_date: date,
) -> AttendancePresenceSession | None:
    return (
        db.query(AttendancePresenceSession)
        .filter(
            AttendancePresenceSession.tenant_id == tenant_id,
            AttendancePresenceSession.employee_id == employee_id,
            AttendancePresenceSession.attendance_date == attendance_date,
        )
        .order_by(
            AttendancePresenceSession.started_at.desc(),
            AttendancePresenceSession.created_at.desc(),
        )
        .one_or_none()
    )


def _upsert_presence_session(
    db: Session,
    *,
    tenant_id: str,
    employee_id: str,
    attendance_date: date,
    session_type: str,
    session_time: datetime,
    latest_source: str | None,
    camera_id: str | None,
    reason: str | None,
) -> AttendancePresenceSession:
    current = _latest_presence_session(db, tenant_id, employee_id, attendance_date)
    if current is not None and current.session_type == session_type and current.ended_at is None:
        current.latest_source = latest_source
        current.camera_id = camera_id
        current.reason = reason
        return current

    if current is not None and current.session_type != session_type and current.ended_at is None:
        current.ended_at = session_time
        current.latest_source = latest_source
        current.camera_id = camera_id
        current.reason = reason
        db.add(current)

    session = AttendancePresenceSession(
        tenant_id=tenant_id,
        employee_id=employee_id,
        attendance_date=attendance_date,
        session_type=session_type,
        started_at=session_time,
        ended_at=None,
        latest_source=latest_source,
        camera_id=camera_id,
        reason=reason,
    )
    db.add(session)
    return session


def _sync_presence_sessions(
    db: Session,
    *,
    tenant_id: str,
    attendance_date: date,
    rows: list[dict],
    now_utc: datetime,
) -> list[AttendancePresenceSession]:
    synced: list[AttendancePresenceSession] = []
    for row in rows:
        status = row["status"]
        if status == "holiday":
            continue
        session_type = "present" if status == "present" else "absent"
        if session_type == "present":
            session_time = row["last_seen_time"] or row["latest_event_time"] or now_utc
        else:
            session_time = now_utc
        session = _upsert_presence_session(
            db,
            tenant_id=tenant_id,
            employee_id=row["employee_id"],
            attendance_date=attendance_date,
            session_type=session_type,
            session_time=session_time,
            latest_source=row.get("latest_source"),
            camera_id=row.get("camera_id"),
            reason=row.get("reason"),
        )
        synced.append(session)
    db.commit()
    return synced


def _list_presence_sessions(
    db: Session,
    *,
    tenant_id: str,
    attendance_date: date,
) -> list[AttendancePresenceSession]:
    return (
        db.query(AttendancePresenceSession)
        .filter(
            AttendancePresenceSession.tenant_id == tenant_id,
            AttendancePresenceSession.attendance_date == attendance_date,
        )
        .order_by(
            AttendancePresenceSession.employee_id.asc(),
            AttendancePresenceSession.started_at.asc(),
            AttendancePresenceSession.created_at.asc(),
        )
        .all()
    )


def _presence_session_to_dict(session: AttendancePresenceSession) -> dict:
    return {
        "id": session.id,
        "tenant_id": session.tenant_id,
        "employee_id": session.employee_id,
        "attendance_date": session.attendance_date,
        "session_type": session.session_type,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "latest_source": session.latest_source,
        "camera_id": session.camera_id,
        "reason": session.reason,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def _build_latest_camera_matches(
    db: Session,
    *,
    tenant_id: str,
    employee_ids: list[str],
    start_utc: datetime,
    end_utc: datetime,
) -> dict[str, CameraEvent]:
    if not employee_ids:
        return {}
    rows = (
        db.query(CameraEvent)
        .filter(
            CameraEvent.tenant_id == tenant_id,
            CameraEvent.employee_id.in_(employee_ids),
            CameraEvent.created_at >= start_utc,
            CameraEvent.created_at < end_utc,
            CameraEvent.recognition_status == "MATCHED",
        )
        .order_by(CameraEvent.created_at.desc())
        .all()
    )
    latest_matches: dict[str, CameraEvent] = {}
    for event in rows:
        employee_id = str(event.employee_id)
        if employee_id not in latest_matches:
            latest_matches[employee_id] = event
    return latest_matches


def _count_camera_events(
    db: Session,
    tenant_id: str,
    start_utc: datetime,
    end_utc: datetime,
) -> tuple[int, int, str | None, datetime | None]:
    camera_events = (
        db.query(CameraEvent)
        .filter(
            CameraEvent.tenant_id == tenant_id,
            CameraEvent.created_at >= start_utc,
            CameraEvent.created_at < end_utc,
        )
        .order_by(CameraEvent.created_at.desc())
        .all()
    )
    unknown_face_count = sum(1 for event in camera_events if event.recognition_status == "UNKNOWN")
    no_face_count = sum(1 for event in camera_events if event.recognition_status == "NO_FACE")
    latest_recognition_result = next(
        (event.recognition_status for event in camera_events if event.recognition_status != "FRAME_CAPTURED"),
        camera_events[0].recognition_status if camera_events else None,
    )
    last_camera_frame_time = camera_events[0].created_at if camera_events else None
    return unknown_face_count, no_face_count, latest_recognition_result, last_camera_frame_time


def _active_attendance_camera_count(db: Session, tenant_id: str) -> int:
    return (
        db.query(Camera.id)
        .filter(
            Camera.tenant_id == tenant_id,
            Camera.is_active.is_(True),
            Camera.assigned_feature_scope.in_(("attendance", "both")),
        )
        .count()
    )


def _build_employee_sessions(events: list[AttendanceEvent], now_utc: datetime) -> list[dict]:
    sessions: list[dict] = []
    open_event: AttendanceEvent | None = None
    for event in events:
        if event.event_type == "check_in":
            if open_event is not None:
                duration = max(0, int((event.event_time - open_event.event_time).total_seconds() // 60))
                sessions.append({
                    "check_in": open_event.event_time,
                    "check_out": event.event_time,
                    "duration_minutes": duration,
                    "source": open_event.source,
                    "camera_id": open_event.camera_id,
                    "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
                    "is_open": False,
                })
            open_event = event
        elif event.event_type == "check_out":
            if open_event is not None:
                duration = max(0, int((event.event_time - open_event.event_time).total_seconds() // 60))
                sessions.append({
                    "check_in": open_event.event_time,
                    "check_out": event.event_time,
                    "duration_minutes": duration,
                    "source": open_event.source,
                    "camera_id": open_event.camera_id,
                    "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
                    "is_open": False,
                })
                open_event = None
    if open_event is not None:
        duration = max(0, int((now_utc - open_event.event_time).total_seconds() // 60))
        sessions.append({
            "check_in": open_event.event_time,
            "check_out": None,
            "duration_minutes": duration,
            "source": open_event.source,
            "camera_id": open_event.camera_id,
            "confidence": float(open_event.confidence) if open_event.confidence is not None else None,
            "is_open": True,
        })
    return sessions


def _live_camera_status(db: Session, tenant_id: str) -> dict:
    camera = (
        db.query(Camera)
        .filter(
            Camera.tenant_id == tenant_id,
            Camera.assigned_feature_scope.in_(("attendance", "both")),
        )
        .order_by(Camera.is_active.desc(), Camera.last_seen_at.desc().nullslast(), Camera.updated_at.desc())
        .first()
    )
    if camera is None:
        return {
            "camera_id": None,
            "camera_name": None,
            "enabled": False,
            "health_status": "unknown",
            "last_frame_at": None,
        }
    return {
        "camera_id": camera.id,
        "camera_name": camera.name,
        "enabled": bool(camera.is_active),
        "health_status": camera.health_status,
        "last_frame_at": camera.last_seen_at,
    }


def _unknown_face_attempt_count(db: Session, tenant_id: str, start_utc: datetime, end_utc: datetime) -> int:
    return (
        db.query(CameraEvent.id)
        .filter(
            CameraEvent.tenant_id == tenant_id,
            CameraEvent.created_at >= start_utc,
            CameraEvent.created_at < end_utc,
            CameraEvent.recognition_status == "UNKNOWN",
        )
        .count()
    )


def get_attendance_board(
    db: Session,
    tenant_id: str,
    *,
    attendance_date: date | str | None = None,
    search: str | None = None,
    department: str | None = None,
    shift_id: str | None = None,
    status_filter: str | None = None,
) -> dict:
    """Return the attendance board projection for a tenant and date."""
    tenant_zone = _tenant_zone(db, tenant_id)
    selected_date = _parse_attendance_board_date(attendance_date, tenant_zone)
    now_utc = datetime.now(timezone.utc)
    start_utc, end_utc = _selected_day_bounds(selected_date, tenant_zone)
    is_holiday = _is_holiday(db, tenant_id, selected_date)
    is_working_day = _is_working_day(db, tenant_id, selected_date)

    employee_query = db.query(AttendanceEmployee).filter(
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.is_active.is_(True),
    )
    if search:
        term = f"%{search.strip()}%"
        employee_query = employee_query.filter(
            or_(
                AttendanceEmployee.full_name.ilike(term),
                AttendanceEmployee.employee_code.ilike(term),
                AttendanceEmployee.email.ilike(term),
            )
        )
    if department:
        employee_query = employee_query.filter(AttendanceEmployee.department == department)
    if shift_id:
        employee_query = employee_query.filter(AttendanceEmployee.shift_id == shift_id)

    employees = employee_query.order_by(AttendanceEmployee.full_name.asc()).all()
    employee_ids = [employee.id for employee in employees]
    live_presence_window_seconds = max(app_settings.camera_frame_interval_seconds * 3, 10)
    live_presence_cutoff = now_utc - timedelta(seconds=live_presence_window_seconds)

    records = {}
    if employee_ids:
        for record in db.query(DailyAttendanceRecord).filter(
            DailyAttendanceRecord.tenant_id == tenant_id,
            DailyAttendanceRecord.attendance_date == selected_date,
            DailyAttendanceRecord.employee_id.in_(employee_ids),
            ).all():
            records[record.employee_id] = record

    latest_camera_matches = _build_latest_camera_matches(
        db,
        tenant_id=tenant_id,
        employee_ids=employee_ids,
        start_utc=start_utc,
        end_utc=end_utc,
    )

    shifts = {shift.id: shift for shift in db.query(AttendanceShift).filter(AttendanceShift.tenant_id == tenant_id).all()}
    default_shift = next((shift for shift in shifts.values() if shift.is_default and shift.is_active), None)

    events_by_employee: dict[str, list[AttendanceEvent]] = {employee_id: [] for employee_id in employee_ids}
    if employee_ids:
        events = db.query(AttendanceEvent).filter(
            AttendanceEvent.tenant_id == tenant_id,
            AttendanceEvent.employee_id.in_(employee_ids),
            AttendanceEvent.event_time >= start_utc,
            AttendanceEvent.event_time < end_utc,
        ).order_by(AttendanceEvent.event_time.asc()).all()
        for event in events:
            events_by_employee.setdefault(event.employee_id, []).append(event)

    camera_names = {
        camera.id: camera.name
        for camera in db.query(Camera)
        .filter(Camera.tenant_id == tenant_id)
        .all()
    }

    rows: list[dict] = []
    session_rows: list[dict] = []
    present_employees: list[dict] = []
    absent_employees: list[dict] = []
    latest_sessions = _build_latest_session_rows(
        db=db,
        tenant_id=tenant_id,
        selected_date=selected_date,
        start_utc=start_utc,
        end_utc=end_utc,
        camera_names=camera_names,
    )
    unknown_face_count, no_face_count, last_recognition_result, last_camera_frame_time = _count_camera_events(
        db,
        tenant_id,
        start_utc,
        end_utc,
    )
    active_attendance_camera_count = _active_attendance_camera_count(db, tenant_id)
    stats = {
        "total": 0,
        "present": 0,
        "late": 0,
        "absent": 0,
        "half_day": 0,
        "holiday": 0,
        "not_detected": 0,
        "unknown_face_attempts": unknown_face_count,
    }

    for employee in employees:
        record = records.get(employee.id)
        shift = shifts.get(employee.shift_id) if employee.shift_id else default_shift
        latest_camera_match = latest_camera_matches.get(employee.id)
        live_present = latest_camera_match is not None and latest_camera_match.created_at >= live_presence_cutoff
        if live_present:
            status = "present"
        elif is_holiday and record is None:
            status = "holiday"
        elif selected_date > now_utc.astimezone(tenant_zone).date():
            status = "not_detected"
        elif selected_date < now_utc.astimezone(tenant_zone).date():
            status = "absent"
        else:
            cutoff_local = _board_cutoff_local(
                attendance_date=selected_date,
                tenant_zone=tenant_zone,
                shift=shift,
            )
            if cutoff_local is not None and now_utc.astimezone(tenant_zone) > cutoff_local:
                status = "absent"
            else:
                status = "not_detected"
        sessions = _build_employee_sessions(events_by_employee.get(employee.id, []), now_utc)
        present_minutes = _daily_present_minutes(record, attendance_date=selected_date, tenant_zone=tenant_zone, now_utc=now_utc)
        if present_minutes == 0 and sessions:
            present_minutes = sum(int(session["duration_minutes"] or 0) for session in sessions)
        expected_minutes = int(shift.full_day_min_minutes) if shift else 0
        absent_minutes = max(0, expected_minutes - present_minutes) if status in {"absent", "late", "half_day", "present", "not_detected"} else 0
        latest_event = events_by_employee.get(employee.id, [])[-1] if events_by_employee.get(employee.id) else None
        reason = _board_employee_reason(
            status=status,
            attendance_date=selected_date,
            tenant_zone=tenant_zone,
            shift=shift,
            now_utc=now_utc,
            is_holiday=is_holiday,
            is_working_day=is_working_day,
            latest_event=latest_camera_match or latest_event,
        )
        row = _build_board_employee_row(
            employee=employee,
            record=record,
            latest_event=latest_camera_match or latest_event,
            status=status,
            reason=reason,
            work_minutes=present_minutes,
            sessions=sessions,
        )
        row["shift_name"] = shift.name if shift else None
        row["first_seen_at"] = record.first_check_in if record else (sessions[0]["check_in"] if sessions else None)
        row["last_seen_at"] = (
            latest_camera_match.created_at
            if latest_camera_match is not None
            else record.last_check_out if record and record.last_check_out else (latest_event.event_time if latest_event else None)
        )
        row["total_present_minutes"] = present_minutes
        row["total_absent_minutes"] = absent_minutes
        row["latest_event_source"] = row["latest_source"]
        row["latest_confidence"] = float(latest_camera_match.confidence) if latest_camera_match and latest_camera_match.confidence is not None else (
            float(latest_event.confidence) if latest_event and latest_event.confidence is not None else None
        )
        row["attendance_message"] = reason
        session_rows.append(row)
        if status_filter and status_filter != "all" and row["status"] != status_filter:
            continue
        rows.append(row)
        stats["total"] += 1
        if row["status"] in stats:
            stats[row["status"]] += 1
        if row["status"] == "present":
            present_employees.append(row)
        elif row["status"] in {"absent", "not_detected"}:
            absent_employees.append(row)

    _sync_presence_sessions(
        db,
        tenant_id=tenant_id,
        attendance_date=selected_date,
        rows=session_rows,
        now_utc=now_utc,
    )
    presence_sessions = _list_presence_sessions(
        db,
        tenant_id=tenant_id,
        attendance_date=selected_date,
    )

    latest_sessions.sort(
        key=lambda item: item["event_time"] or datetime.min.replace(tzinfo=timezone.utc),
        reverse=True,
    )

    debug_summary = {
        "tenant_id": tenant_id,
        "selected_date": selected_date,
        "total_active_employees": len(employees),
        "present_count": len(present_employees),
        "absent_count": len([row for row in absent_employees if row["status"] == "absent"]),
        "not_detected_count": len([row for row in absent_employees if row["status"] == "not_detected"]),
        "holiday_count": len([row for row in rows if row["status"] == "holiday"]),
        "latest_event_time": latest_sessions[0]["event_time"] if latest_sessions else None,
        "active_attendance_camera_count": active_attendance_camera_count,
        "camera_enabled": active_attendance_camera_count > 0,
        "last_camera_frame_time": last_camera_frame_time,
        "last_recognition_result": last_recognition_result,
        "unknown_face_count": unknown_face_count,
        "no_face_count": no_face_count,
        "live_presence_window_seconds": live_presence_window_seconds,
    }

    logger.info(
        (
            "[ATTENDANCE_BOARD] tenant_id=%s selected_date=%s active_employees=%s present_count=%s "
            "absent_count=%s not_detected_count=%s latest_event_time=%s active_attendance_camera_count=%s"
        ),
        tenant_id,
        selected_date.isoformat(),
        debug_summary["total_active_employees"],
        debug_summary["present_count"],
        debug_summary["absent_count"],
        debug_summary["not_detected_count"],
        debug_summary["latest_event_time"].isoformat() if debug_summary["latest_event_time"] else "-",
        active_attendance_camera_count,
    )

    return {
        "attendance_date": selected_date,
        "generated_at": now_utc,
        "stats": stats,
        "employees": rows,
        "present_employees": present_employees,
        "absent_employees": absent_employees,
        "latest_sessions": latest_sessions,
        "presence_sessions": [_presence_session_to_dict(session) for session in presence_sessions],
        "debug_summary": debug_summary,
        "live_camera_status": {
            "camera_id": None,
            "camera_name": None,
            "enabled": bool(active_attendance_camera_count),
            "health_status": "online" if active_attendance_camera_count else "unknown",
            "last_frame_at": last_camera_frame_time,
        },
    }


def get_employee_attendance_summary(
    db: Session,
    tenant_id: str,
    employee_id: str,
    *,
    attendance_date: date | str | None = None,
) -> dict | None:
    tenant_zone = _tenant_zone(db, tenant_id)
    selected_date = _parse_attendance_board_date(attendance_date, tenant_zone)
    now_utc = datetime.now(timezone.utc)
    start_utc, end_utc = _selected_day_bounds(selected_date, tenant_zone)

    employee = db.query(AttendanceEmployee).filter(
        AttendanceEmployee.tenant_id == tenant_id,
        AttendanceEmployee.id == employee_id,
        AttendanceEmployee.is_active.is_(True),
    ).one_or_none()
    if employee is None:
        return None

    board = get_attendance_board(db, tenant_id, attendance_date=selected_date)
    board_row = next((row for row in board["employees"] if row["employee_id"] == employee_id), None)
    events = db.query(AttendanceEvent).filter(
        AttendanceEvent.tenant_id == tenant_id,
        AttendanceEvent.employee_id == employee_id,
        AttendanceEvent.event_time >= start_utc,
        AttendanceEvent.event_time < end_utc,
    ).order_by(AttendanceEvent.event_time.asc()).all()
    sessions = _build_employee_sessions(events, now_utc)
    presence_sessions = [
        _presence_session_to_dict(session)
        for session in _list_presence_sessions(
            db,
            tenant_id=tenant_id,
            attendance_date=selected_date,
        )
        if session.employee_id == employee.id
    ]
    detection_history = [
        {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "camera_id": event.camera_id,
            "confidence": float(event.confidence) if event.confidence is not None else None,
            "event_time": event.event_time,
            "metadata": event.event_metadata or {},
        }
        for event in events
    ]
    return {
        "attendance_date": selected_date,
        "employee": {
            "id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "email": employee.email,
            "department": employee.department,
            "designation": employee.designation,
        },
        "summary": board_row,
        "sessions": sessions,
        "presence_sessions": presence_sessions,
        "detection_history": detection_history,
    }

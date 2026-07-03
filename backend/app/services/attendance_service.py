"""Attendance service helpers."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings as app_settings
from app.models.attendance import (
    AttendanceEvent,
    AttendanceHoliday,
    AttendanceSettings,
    AttendanceShift,
    AttendanceWorkingDay,
    DailyAttendanceRecord,
)
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

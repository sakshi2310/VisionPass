"""Tenant-user self-service queries, always scoped to the authenticated member."""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.models.attendance import AttendanceSettings, AttendanceShift, DailyAttendanceRecord
from app.models.employee import AttendanceEmployee, EmployeeFaceProfile
from app.models.tenant_member import TenantMember

DEFAULT_TIMEZONE = "Asia/Kolkata"


def _tenant_zone(db: Session, tenant_id: str) -> ZoneInfo:
    timezone_name = (
        db.query(AttendanceSettings.timezone)
        .filter(AttendanceSettings.tenant_id == tenant_id)
        .scalar()
        or DEFAULT_TIMEZONE
    )
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo(DEFAULT_TIMEZONE)


def _employee_for_member(db: Session, member: TenantMember) -> AttendanceEmployee | None:
    if not member.employee_id:
        return None
    return (
        db.query(AttendanceEmployee)
        .filter(
            cast(AttendanceEmployee.id, String) == member.employee_id,
            AttendanceEmployee.tenant_id == member.tenant_id,
        )
        .one_or_none()
    )


def _shift_for_employee(
    db: Session,
    tenant_id: str,
    employee: AttendanceEmployee | None,
) -> AttendanceShift | None:
    if employee is None:
        return None
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


def _shift_dict(shift: AttendanceShift | None) -> dict | None:
    if shift is None:
        return None
    return {
        "id": shift.id,
        "name": shift.name,
        "start_time": shift.start_time,
        "end_time": shift.end_time,
        "grace_period_minutes": shift.grace_period_minutes,
    }


def _month_dates(month: str | None, today: date) -> tuple[str, date, date]:
    normalized = month or today.strftime("%Y-%m")
    try:
        start = datetime.strptime(normalized, "%Y-%m").date().replace(day=1)
    except ValueError as exc:
        raise ValueError("month must use YYYY-MM format") from exc
    end = start.replace(day=monthrange(start.year, start.month)[1])
    return normalized, start, end


def _monthly_summary(month: str, rows: list[DailyAttendanceRecord]) -> dict:
    counts = {status: 0 for status in ("present", "late", "half_day", "absent", "holiday")}
    for row in rows:
        counts[row.status] = counts.get(row.status, 0) + 1
    attended = counts["present"] + counts["late"] + counts["half_day"]
    working_days = attended + counts["absent"]
    return {
        "month": month,
        "present": counts["present"],
        "late": counts["late"],
        "half_day": counts["half_day"],
        "absent": counts["absent"],
        "holidays": counts["holiday"],
        "total_working_days": working_days,
        "total_work_hours": round(sum(row.total_work_minutes for row in rows) / 60, 2),
        "attendance_percentage": round((attended / working_days) * 100, 1) if working_days else 0,
    }


def get_me_attendance(db: Session, member: TenantMember, month: str | None = None) -> dict:
    employee = _employee_for_member(db, member)
    today = datetime.now(_tenant_zone(db, member.tenant_id)).date()
    normalized_month, start, end = _month_dates(month, today)
    if employee is None:
        return {
            "month": normalized_month,
            "days": [],
            "summary": _monthly_summary(normalized_month, []),
            "employee_linked": False,
        }

    rows = (
        db.query(DailyAttendanceRecord)
        .filter(
            DailyAttendanceRecord.tenant_id == member.tenant_id,
            DailyAttendanceRecord.employee_id == employee.id,
            DailyAttendanceRecord.attendance_date >= start,
            DailyAttendanceRecord.attendance_date <= end,
        )
        .order_by(DailyAttendanceRecord.attendance_date.desc())
        .all()
    )
    shifts = {
        shift.id: shift
        for shift in db.query(AttendanceShift)
        .filter(
            AttendanceShift.tenant_id == member.tenant_id,
            AttendanceShift.id.in_({row.shift_id for row in rows if row.shift_id}),
        )
        .all()
    } if any(row.shift_id for row in rows) else {}
    return {
        "month": normalized_month,
        "days": [
            {
                "id": row.id,
                "attendance_date": row.attendance_date,
                "first_check_in": row.first_check_in,
                "last_check_out": row.last_check_out,
                "total_work_minutes": row.total_work_minutes,
                "working_hours": round(row.total_work_minutes / 60, 2),
                "status": row.status,
                "shift": _shift_dict(shifts.get(row.shift_id)),
            }
            for row in rows
        ],
        "summary": _monthly_summary(normalized_month, rows),
        "employee_linked": True,
    }


def get_me_dashboard(db: Session, member: TenantMember) -> dict:
    zone = _tenant_zone(db, member.tenant_id)
    now = datetime.now(timezone.utc)
    today = now.astimezone(zone).date()
    employee = _employee_for_member(db, member)
    month_data = get_me_attendance(db, member, today.strftime("%Y-%m"))
    shift = _shift_for_employee(db, member.tenant_id, employee)
    record = None
    if employee is not None:
        record = (
            db.query(DailyAttendanceRecord)
            .filter(
                DailyAttendanceRecord.tenant_id == member.tenant_id,
                DailyAttendanceRecord.employee_id == employee.id,
                DailyAttendanceRecord.attendance_date == today,
            )
            .one_or_none()
        )

    work_minutes = record.total_work_minutes if record else 0
    if record and record.first_check_in and not record.last_check_out:
        work_minutes = max(0, int((now - record.first_check_in).total_seconds() // 60))
        if shift:
            work_minutes = max(0, work_minutes - shift.break_duration_minutes)
    return {
        "today_status": record.status if record else "not_marked",
        "check_in_time": record.first_check_in if record else None,
        "check_out_time": record.last_check_out if record else None,
        "working_hours": round(work_minutes / 60, 2),
        "current_shift": _shift_dict(shift),
        "monthly_summary": month_data["summary"],
        "employee_linked": employee is not None,
    }


def get_me_profile(db: Session, member: TenantMember) -> dict:
    employee = _employee_for_member(db, member)
    shift = _shift_for_employee(db, member.tenant_id, employee)
    face_profile = None
    if employee is not None:
        face_profile = (
            db.query(EmployeeFaceProfile)
            .filter(
                EmployeeFaceProfile.tenant_id == member.tenant_id,
                EmployeeFaceProfile.employee_id == employee.id,
            )
            .one_or_none()
        )
    return {
        "member_id": member.id,
        "employee_id": employee.id if employee else None,
        "full_name": employee.full_name if employee else member.full_name,
        "email": employee.email if employee else member.email,
        "phone": member.phone or (employee.mobile if employee else None),
        "department": (employee.department if employee else None) or member.department,
        "designation": (employee.designation if employee else None) or member.designation,
        "employee_code": employee.employee_code if employee else None,
        "employee_type": employee.employee_type if employee else None,
        "joining_date": employee.joining_date if employee else None,
        "status": ("active" if employee.is_active else "inactive") if employee else member.status,
        "shift": _shift_dict(shift),
        "face_enrollment_status": face_profile.enrollment_status if face_profile else "Not Enrolled",
        "face_count": face_profile.face_count if face_profile else 0,
    }


def get_me_notifications(db: Session, member: TenantMember) -> list[dict]:
    employee = _employee_for_member(db, member)
    notifications: list[dict] = []
    if employee is None:
        return [{
            "id": f"profile-{member.id}",
            "type": "profile",
            "title": "Attendance profile not linked",
            "message": "Ask your administrator to link your account to an employee record.",
            "severity": "warning",
            "created_at": member.updated_at,
        }]

    rows = (
        db.query(DailyAttendanceRecord)
        .filter(
            DailyAttendanceRecord.tenant_id == member.tenant_id,
            DailyAttendanceRecord.employee_id == employee.id,
            DailyAttendanceRecord.status.in_(("late", "half_day", "absent")),
        )
        .order_by(DailyAttendanceRecord.attendance_date.desc())
        .limit(30)
        .all()
    )
    labels = {
        "late": ("Late arrival recorded", "Your attendance was marked late."),
        "half_day": ("Half day recorded", "Your worked hours were recorded as a half day."),
        "absent": ("Absence recorded", "Your attendance was marked absent."),
    }
    for row in rows:
        title, message = labels[row.status]
        notifications.append({
            "id": f"attendance-{row.id}",
            "type": "attendance",
            "title": title,
            "message": f"{message} Date: {row.attendance_date.isoformat()}.",
            "severity": "warning",
            "created_at": row.updated_at,
        })
    return notifications

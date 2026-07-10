"""Tenant-scoped operational report queries."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import and_, func, literal
from sqlalchemy.orm import Session

from app.models.access_event import AccessLog
from app.models.attendance import AttendanceEvent, DailyAttendanceRecord
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee
from app.models.person_detection import PersonDetection
from app.models.visitor import Visitor, VisitorVisit


def _datetime_bounds(start_date: date | None, end_date: date | None) -> tuple[datetime | None, datetime | None]:
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc) if start_date else None
    end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=timezone.utc) if end_date else None
    return start, end


def _apply_datetime_range(query, column, start_date: date | None, end_date: date | None):
    start, end = _datetime_bounds(start_date, end_date)
    if start is not None:
        query = query.filter(column >= start)
    if end is not None:
        query = query.filter(column < end)
    return query


def attendance_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
) -> list[dict]:
    query = (
        db.query(DailyAttendanceRecord, AttendanceEmployee)
        .join(
            AttendanceEmployee,
            and_(
                AttendanceEmployee.id == DailyAttendanceRecord.employee_id,
                AttendanceEmployee.tenant_id == tenant_id,
            ),
        )
        .filter(DailyAttendanceRecord.tenant_id == tenant_id)
    )
    if start_date:
        query = query.filter(DailyAttendanceRecord.attendance_date >= start_date)
    if end_date:
        query = query.filter(DailyAttendanceRecord.attendance_date <= end_date)
    if employee_id:
        query = query.filter(DailyAttendanceRecord.employee_id == employee_id)
    if department:
        query = query.filter(func.lower(AttendanceEmployee.department) == department.strip().lower())
    if status:
        query = query.filter(DailyAttendanceRecord.status == status.strip().lower())
    if camera_id or event_type:
        event_match = db.query(AttendanceEvent.id).filter(
            AttendanceEvent.tenant_id == tenant_id,
            AttendanceEvent.employee_id == DailyAttendanceRecord.employee_id,
            func.date(AttendanceEvent.event_time) == DailyAttendanceRecord.attendance_date,
        )
        if camera_id:
            event_match = event_match.filter(AttendanceEvent.camera_id == camera_id)
        if event_type:
            event_match = event_match.filter(AttendanceEvent.event_type == event_type.strip().lower())
        query = query.filter(event_match.exists())

    rows = query.order_by(DailyAttendanceRecord.attendance_date.desc(), AttendanceEmployee.full_name).all()
    return [
        {
            "id": record.id,
            "attendance_date": record.attendance_date,
            "employee_id": employee.id,
            "employee_code": employee.employee_code,
            "employee_name": employee.full_name,
            "department": employee.department,
            "status": record.status,
            "first_check_in": record.first_check_in,
            "last_check_out": record.last_check_out,
            "total_work_minutes": record.total_work_minutes,
        }
        for record, employee in rows
    ]


def employee_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = db.query(AttendanceEmployee).filter(AttendanceEmployee.tenant_id == tenant_id)
    query = _apply_datetime_range(query, AttendanceEmployee.created_at, start_date, end_date)
    if employee_id:
        query = query.filter(AttendanceEmployee.id == employee_id)
    if department:
        query = query.filter(func.lower(AttendanceEmployee.department) == department.strip().lower())
    if status:
        normalized = status.strip().lower()
        if normalized in {"active", "inactive"}:
            query = query.filter(AttendanceEmployee.is_active.is_(normalized == "active"))
    rows = query.order_by(AttendanceEmployee.full_name).all()
    return [
        {
            "id": row.id,
            "employee_code": row.employee_code,
            "full_name": row.full_name,
            "email": row.email,
            "department": row.department,
            "designation": row.designation,
            "employee_type": row.employee_type,
            "status": "active" if row.is_active else "inactive",
            "joining_date": row.joining_date,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def visitor_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    match_type: str | None = None,
) -> list[dict]:
    query = (
        db.query(VisitorVisit, Visitor, Camera, PersonDetection)
        .join(Visitor, and_(Visitor.id == VisitorVisit.visitor_id, Visitor.tenant_id == tenant_id))
        .outerjoin(Camera, and_(Camera.id == VisitorVisit.camera_id, Camera.tenant_id == tenant_id))
        .outerjoin(PersonDetection, and_(PersonDetection.id == VisitorVisit.person_detection_id, PersonDetection.tenant_id == tenant_id))
        .filter(VisitorVisit.tenant_id == tenant_id)
    )
    range_column = VisitorVisit.seen_at
    query = _apply_datetime_range(query, range_column, start_date, end_date)
    if employee_id:
        query = query.filter(Visitor.id == employee_id)
    if status:
        query = query.filter(Visitor.status == status.strip().lower())
    if camera_id:
        query = query.filter(VisitorVisit.camera_id == camera_id)
    if zone_id:
        query = query.filter(VisitorVisit.zone_id == zone_id)
    if match_type:
        query = query.filter(func.coalesce(PersonDetection.match_type, literal("visitor")) == match_type)
    rows = query.order_by(range_column.desc()).all()
    return [
        {
            "id": visit.id,
            "visitor_id": visitor.id,
            "full_name": visitor.full_name,
            "phone": visitor.phone,
            "company": visitor.company,
            "purpose": visitor.purpose,
            "status": visitor.status,
            "match_type": detection.match_type if detection is not None else "visitor",
            "access_status": visit.access_status,
            "camera_id": camera.id if camera else visit.camera_id,
            "camera_name": camera.name if camera else None,
            "zone_id": visit.zone_id,
            "seen_at": visit.seen_at,
            "snapshot_url": visit.snapshot_url,
            "check_in_time": visit.check_in_time,
            "check_out_time": visit.check_out_time,
            "note": detection.note if detection else visit.notes,
            "image_path": visit.image_path,
            "first_seen_at": visitor.first_seen_at,
            "last_seen_at": visitor.last_seen_at,
            "total_visits": visitor.total_visits,
            "created_at": visitor.created_at,
        }
        for visit, visitor, camera, detection in rows
    ]


def person_detection_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    match_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = (
        db.query(PersonDetection, Camera)
        .join(Camera, and_(Camera.id == PersonDetection.camera_id, Camera.tenant_id == tenant_id))
        .filter(PersonDetection.tenant_id == tenant_id)
    )
    query = _apply_datetime_range(query, PersonDetection.detected_at, start_date, end_date)
    if camera_id:
        query = query.filter(PersonDetection.camera_id == camera_id)
    if zone_id:
        query = query.filter(PersonDetection.zone_id == zone_id)
    if match_type:
        query = query.filter(PersonDetection.match_type == match_type)
    if status:
        query = query.filter(PersonDetection.status == status.strip().lower())
    rows = query.order_by(PersonDetection.detected_at.desc(), PersonDetection.created_at.desc()).all()
    return [
        {
            "id": detection.id,
            "detected_at": detection.detected_at,
            "camera_id": camera.id,
            "camera_name": camera.name,
            "zone_id": detection.zone_id,
            "match_type": detection.match_type,
            "status": detection.status,
            "note": detection.note,
            "matched_staff_id": detection.matched_staff_id,
            "matched_visitor_id": detection.matched_visitor_id,
            "image_path": detection.image_path,
            "created_at": detection.created_at,
            "updated_at": detection.updated_at,
        }
        for detection, camera in rows
    ]


def unknown_review_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    match_type: str | None = None,
    status: str | None = None,
) -> list[dict]:
    query = (
        db.query(PersonDetection, Camera)
        .join(Camera, and_(Camera.id == PersonDetection.camera_id, Camera.tenant_id == tenant_id))
        .filter(
            PersonDetection.tenant_id == tenant_id,
            PersonDetection.match_type == "unknown",
            PersonDetection.note.isnot(None),
        )
    )
    query = _apply_datetime_range(query, PersonDetection.detected_at, start_date, end_date)
    if camera_id:
        query = query.filter(PersonDetection.camera_id == camera_id)
    if zone_id:
        query = query.filter(PersonDetection.zone_id == zone_id)
    if match_type:
        query = query.filter(PersonDetection.match_type == match_type)
    if status:
        query = query.filter(PersonDetection.status == status.strip().lower())
    else:
        query = query.filter(PersonDetection.status.in_(["new", "reviewed"]))
    rows = query.order_by(PersonDetection.detected_at.desc(), PersonDetection.created_at.desc()).all()
    return [
        {
            "id": detection.id,
            "detected_at": detection.detected_at,
            "camera_id": camera.id,
            "camera_name": camera.name,
            "zone_id": detection.zone_id,
            "note": detection.note,
            "status": detection.status,
            "match_type": detection.match_type,
            "image_path": detection.image_path,
            "created_at": detection.created_at,
            "updated_at": detection.updated_at,
        }
        for detection, camera in rows
    ]


def camera_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
) -> list[dict]:
    matching_events = db.query(CameraEvent.id).filter(
        CameraEvent.tenant_id == tenant_id,
        CameraEvent.camera_id == Camera.id,
    )
    matching_events = _apply_datetime_range(matching_events, CameraEvent.created_at, start_date, end_date)
    if event_type:
        matching_events = matching_events.filter(CameraEvent.event_type == event_type.strip().lower())
    event_count = matching_events.with_entities(func.count(CameraEvent.id))

    query = db.query(Camera, event_count.scalar_subquery().label("event_count")).filter(Camera.tenant_id == tenant_id)
    if camera_id:
        query = query.filter(Camera.id == camera_id)
    if status:
        normalized = status.strip().lower()
        if normalized in {"active", "inactive"}:
            query = query.filter(Camera.is_active.is_(normalized == "active"))
        else:
            query = query.filter(Camera.health_status == normalized)
    if start_date or end_date or event_type:
        query = query.filter(matching_events.exists())
    rows = query.order_by(Camera.name).all()
    return [
        {
            "id": camera.id,
            "name": camera.name,
            "location": camera.location,
            "camera_type": camera.camera_type,
            "status": "active" if camera.is_active else "inactive",
            "health_status": camera.health_status,
            "last_seen_at": camera.last_seen_at,
            "event_count": count,
            "created_at": camera.created_at,
        }
        for camera, count in rows
    ]


def recognition_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
) -> list[dict]:
    query = (
        db.query(CameraEvent, Camera, AttendanceEmployee)
        .join(Camera, and_(Camera.id == CameraEvent.camera_id, Camera.tenant_id == tenant_id))
        .outerjoin(
            AttendanceEmployee,
            and_(AttendanceEmployee.id == CameraEvent.employee_id, AttendanceEmployee.tenant_id == tenant_id),
        )
        .filter(CameraEvent.tenant_id == tenant_id)
    )
    query = _apply_datetime_range(query, CameraEvent.created_at, start_date, end_date)
    if employee_id:
        query = query.filter(CameraEvent.employee_id == employee_id)
    if department:
        query = query.filter(func.lower(AttendanceEmployee.department) == department.strip().lower())
    if status:
        query = query.filter(func.lower(CameraEvent.recognition_status) == status.strip().lower())
    if camera_id:
        query = query.filter(CameraEvent.camera_id == camera_id)
    if event_type:
        query = query.filter(CameraEvent.event_type == event_type.strip().lower())
    rows = query.order_by(CameraEvent.created_at.desc()).all()
    return [
        {
            "id": event.id,
            "created_at": event.created_at,
            "event_type": event.event_type,
            "recognition_status": event.recognition_status,
            "confidence": event.confidence,
            "employee_id": event.employee_id,
            "employee_name": employee.full_name if employee else None,
            "department": employee.department if employee else None,
            "camera_id": camera.id,
            "camera_name": camera.name,
            "location": camera.location,
        }
        for event, camera, employee in rows
    ]


def access_report(
    db: Session,
    tenant_id: str,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
) -> list[dict]:
    query = (
        db.query(AccessLog, AttendanceEmployee, Visitor, Camera)
        .outerjoin(
            AttendanceEmployee,
            and_(AttendanceEmployee.id == AccessLog.employee_id, AttendanceEmployee.tenant_id == tenant_id),
        )
        .outerjoin(Visitor, and_(Visitor.id == AccessLog.visitor_id, Visitor.tenant_id == tenant_id))
        .outerjoin(Camera, and_(Camera.id == AccessLog.camera_id, Camera.tenant_id == tenant_id))
        .filter(AccessLog.tenant_id == tenant_id)
    )
    query = _apply_datetime_range(query, AccessLog.created_at, start_date, end_date)
    if employee_id:
        query = query.filter(AccessLog.employee_id == employee_id)
    if department:
        query = query.filter(func.lower(AttendanceEmployee.department) == department.strip().lower())
    if status:
        query = query.filter(AccessLog.decision == status.strip().lower())
    if camera_id:
        query = query.filter(AccessLog.camera_id == camera_id)
    if event_type:
        normalized = event_type.strip().lower()
        if normalized == "employee":
            query = query.filter(AccessLog.employee_id.is_not(None))
        elif normalized == "visitor":
            query = query.filter(AccessLog.visitor_id.is_not(None))
        elif normalized == "unknown":
            query = query.filter(and_(AccessLog.employee_id.is_(None), AccessLog.visitor_id.is_(None)))
    rows = query.order_by(AccessLog.created_at.desc()).all()
    return [
        {
            "id": log.id,
            "created_at": log.created_at,
            "identity_type": "employee" if employee else ("visitor" if visitor else "unknown"),
            "identity_name": employee.full_name if employee else (visitor.full_name if visitor else "Unknown"),
            "employee_id": log.employee_id,
            "department": employee.department if employee else None,
            "camera_id": log.camera_id,
            "camera_name": camera.name if camera else None,
            "decision": log.decision,
            "reason": log.reason,
            "confidence": log.confidence,
        }
        for log, employee, visitor, camera in rows
    ]

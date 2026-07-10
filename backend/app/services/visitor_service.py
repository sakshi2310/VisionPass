"""Tenant-scoped visitor lifecycle service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import String, cast
from sqlalchemy.orm import Session

from app.models.employee import AttendanceEmployee
from app.models.visitor import Visitor, VisitorVisit
from app.services.audit_service import add_tenant_audit


class VisitorError(Exception):
    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _validate_host(db: Session, tenant_id: str, employee_id: str | None) -> None:
    if employee_id is None:
        return
    exists = (
        db.query(AttendanceEmployee.id)
        .filter(
            cast(AttendanceEmployee.id, String) == employee_id,
            AttendanceEmployee.tenant_id == tenant_id,
            AttendanceEmployee.is_active.is_(True),
        )
        .first()
    )
    if exists is None:
        raise VisitorError("Host employee not found", status_code=422)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_name(values: dict) -> str | None:
    name = values.get("name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    full_name = values.get("full_name")
    if isinstance(full_name, str) and full_name.strip():
        return full_name.strip()
    return None


def _normalize_path(values: dict) -> str | None:
    for key in ("image_path", "photo_url", "photo_path"):
        value = values.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _touch_seen(visitor: Visitor, seen_at: datetime) -> None:
    if visitor.first_seen_at is None:
        visitor.first_seen_at = seen_at
    visitor.last_seen_at = seen_at
    visitor.total_visits = int(visitor.total_visits or 0) + 1


def _visit_payload(
    visitor: Visitor,
    *,
    seen_at: datetime,
    person_detection_id: str | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    image_path: str | None = None,
    access_status: str = "granted",
    notes: str | None = None,
) -> VisitorVisit:
    return VisitorVisit(
        tenant_id=visitor.tenant_id,
        visitor_id=visitor.id,
        person_detection_id=person_detection_id,
        camera_id=camera_id,
        zone_id=zone_id,
        seen_at=seen_at,
        image_path=image_path,
        check_in_time=seen_at,
        access_status=access_status,
        notes=notes,
    )


def list_visitors(db: Session, tenant_id: str) -> list[Visitor]:
    return (
        db.query(Visitor)
        .filter(Visitor.tenant_id == tenant_id)
        .order_by(Visitor.last_seen_at.desc().nullslast(), Visitor.updated_at.desc(), Visitor.created_at.desc())
        .all()
    )


def get_visitor(db: Session, tenant_id: str, visitor_id: str) -> Visitor | None:
    return (
        db.query(Visitor)
        .filter(cast(Visitor.id, String) == visitor_id, Visitor.tenant_id == tenant_id)
        .one_or_none()
    )


def list_visitor_visits(db: Session, tenant_id: str, visitor_id: str) -> list[VisitorVisit]:
    return (
        db.query(VisitorVisit)
        .filter(
            VisitorVisit.tenant_id == tenant_id,
            cast(VisitorVisit.visitor_id, String) == visitor_id,
        )
        .order_by(VisitorVisit.seen_at.desc(), VisitorVisit.check_in_time.desc())
        .all()
    )


def get_visitor_visits(db: Session, tenant_id: str, visitor_id: str) -> list[VisitorVisit]:
    return list_visitor_visits(db, tenant_id, visitor_id)


def create_visitor(
    db: Session,
    tenant_id: str,
    actor_id: str,
    values: dict,
    *,
    commit: bool = True,
) -> Visitor:
    _validate_host(db, tenant_id, values.get("host_employee_id"))
    name = _normalize_name(values)
    if not name:
        raise VisitorError("Visitor name is required", status_code=422)
    if values.get("status") in {"checked_in", "checked_out"}:
        raise VisitorError("Use the check-in and check-out actions to change visit status", status_code=422)
    visitor = Visitor(
        tenant_id=tenant_id,
        full_name=name,
        phone=values.get("phone"),
        email=values.get("email"),
        company=values.get("company"),
        purpose=values.get("purpose"),
        photo_path=_normalize_path(values),
        face_embedding=values.get("face_embedding"),
        status=(values.get("status") or "active"),
        notes=values.get("notes"),
    )
    db.add(visitor)
    db.flush()
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_created",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"status": visitor.status, "name": visitor.name},
        note=f"Registered visitor {visitor.name}",
    )
    if commit:
        db.commit()
        db.refresh(visitor)
    return visitor


def update_visitor(
    db: Session,
    tenant_id: str,
    visitor_id: str,
    actor_id: str,
    values: dict,
) -> Visitor | None:
    visitor = get_visitor(db, tenant_id, visitor_id)
    if visitor is None:
        return None
    _validate_host(db, tenant_id, values.get("host_employee_id")) if "host_employee_id" in values else None
    name = _normalize_name(values)
    requested_status = values.get("status")
    if requested_status is not None:
        if visitor.status == "checked_in" and requested_status != visitor.status:
            raise VisitorError("Check out the visitor before changing status")
        if requested_status in {"checked_in", "checked_out"} and requested_status != visitor.status:
            raise VisitorError("Use the check-in and check-out actions to change visit status", status_code=422)
    changed = {}
    for field, value in values.items():
        if field in {"name", "full_name"}:
            if name is not None and visitor.full_name != name:
                changed["name"] = {"from": visitor.full_name, "to": name}
                visitor.full_name = name
        elif field in {"image_path", "photo_url", "photo_path"}:
            normalized = _normalize_path(values)
            if visitor.photo_path != normalized:
                changed["photo_path"] = {"from": visitor.photo_path, "to": normalized}
                visitor.photo_path = normalized
        elif field == "notes":
            if visitor.notes != value:
                changed["notes"] = {"from": visitor.notes, "to": value}
                visitor.notes = value
        elif field == "face_embedding":
            if visitor.face_embedding != value:
                changed["face_embedding"] = {"from": visitor.face_embedding, "to": value}
                visitor.face_embedding = value
        elif field in {"phone", "email", "company", "purpose", "status"}:
            if getattr(visitor, field) != value:
                changed[field] = {"from": getattr(visitor, field), "to": value}
                setattr(visitor, field, value)
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_updated",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"changes": changed},
        note=f"Updated visitor {visitor.name}",
    )
    db.commit()
    db.refresh(visitor)
    return visitor


def add_visitor_note(
    db: Session,
    tenant_id: str,
    visitor_id: str,
    actor_id: str,
    note: str,
) -> Visitor | None:
    visitor = get_visitor(db, tenant_id, visitor_id)
    if visitor is None:
        return None
    cleaned = note.strip()
    visitor.notes = f"{visitor.notes}\n{cleaned}" if visitor.notes else cleaned
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_noted",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"note": cleaned},
        note=f"Updated visitor {visitor.name} note",
    )
    db.commit()
    db.refresh(visitor)
    return visitor


def record_visitor_visit(
    db: Session,
    visitor: Visitor,
    *,
    seen_at: datetime | None = None,
    person_detection_id: str | None = None,
    camera_id: str | None = None,
    zone_id: str | None = None,
    image_path: str | None = None,
    access_status: str = "granted",
    notes: str | None = None,
    commit: bool = True,
) -> VisitorVisit:
    timestamp = seen_at or _now()
    _touch_seen(visitor, timestamp)
    visit = _visit_payload(
        visitor,
        seen_at=timestamp,
        person_detection_id=person_detection_id,
        camera_id=camera_id,
        zone_id=zone_id,
        image_path=image_path,
        access_status=access_status,
        notes=notes,
    )
    db.add_all([visitor, visit])
    if commit:
        db.commit()
        db.refresh(visitor)
        db.refresh(visit)
    return visit


def delete_visitor(db: Session, tenant_id: str, visitor_id: str, actor_id: str) -> bool:
    visitor = get_visitor(db, tenant_id, visitor_id)
    if visitor is None:
        return False
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_deleted",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"full_name": visitor.full_name, "status": visitor.status},
        note=f"Deleted visitor {visitor.full_name}",
    )
    db.delete(visitor)
    db.commit()
    return True


def check_in_visitor(
    db: Session,
    tenant_id: str,
    visitor_id: str,
    actor_id: str,
    *,
    access_status: str,
    notes: str | None,
) -> tuple[Visitor, VisitorVisit] | None:
    visitor = get_visitor(db, tenant_id, visitor_id)
    if visitor is None:
        return None
    if visitor.status == "blocked":
        raise VisitorError("Blocked visitors cannot be checked in")
    visit = record_visitor_visit(
        db,
        visitor,
        access_status=access_status,
        notes=notes,
        commit=False,
    )
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_checked_in",
        entity_type="visitor_visit",
        entity_id=visit.id,
        details={"visitor_id": visitor.id, "access_status": access_status},
        note=f"Checked in visitor {visitor.name}",
    )
    db.commit()
    db.refresh(visitor)
    db.refresh(visit)
    return visitor, visit


def check_out_visitor(
    db: Session,
    tenant_id: str,
    visitor_id: str,
    actor_id: str,
    *,
    notes: str | None,
) -> tuple[Visitor, VisitorVisit] | None:
    visitor = get_visitor(db, tenant_id, visitor_id)
    if visitor is None:
        return None
    if visitor.status == "blocked":
        raise VisitorError("Blocked visitors cannot be checked out")
    visit = (
        db.query(VisitorVisit)
        .filter(
            VisitorVisit.tenant_id == tenant_id,
            VisitorVisit.visitor_id == visitor.id,
            VisitorVisit.check_out_time.is_(None),
        )
        .order_by(VisitorVisit.seen_at.desc(), VisitorVisit.check_in_time.desc())
        .first()
    )
    if visit is None:
        raise VisitorError("Active visitor visit was not found")

    visit.check_out_time = datetime.now(timezone.utc)
    if notes:
        visit.notes = f"{visit.notes}\n{notes}" if visit.notes else notes
    db.add_all([visitor, visit])
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_checked_out",
        entity_type="visitor_visit",
        entity_id=visit.id,
        details={"visitor_id": visitor.id},
        note=f"Checked out visitor {visitor.name}",
    )
    db.commit()
    db.refresh(visitor)
    db.refresh(visit)
    return visitor, visit

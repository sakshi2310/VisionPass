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


def list_visitors(db: Session, tenant_id: str) -> list[Visitor]:
    return (
        db.query(Visitor)
        .filter(Visitor.tenant_id == tenant_id)
        .order_by(Visitor.updated_at.desc(), Visitor.created_at.desc())
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
        .order_by(VisitorVisit.check_in_time.desc())
        .all()
    )


def create_visitor(
    db: Session,
    tenant_id: str,
    actor_id: str,
    values: dict,
) -> Visitor:
    _validate_host(db, tenant_id, values.get("host_employee_id"))
    if values.get("status") in {"checked_in", "checked_out"}:
        raise VisitorError("Use the check-in and check-out actions to change visit status", status_code=422)
    visitor = Visitor(tenant_id=tenant_id, **values)
    db.add(visitor)
    db.flush()
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_created",
        entity_type="visitor",
        entity_id=visitor.id,
        details={"status": visitor.status, "full_name": visitor.full_name},
        note=f"Registered visitor {visitor.full_name}",
    )
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
    requested_status = values.get("status")
    if requested_status is not None:
        if visitor.status == "checked_in" and requested_status != visitor.status:
            raise VisitorError("Check out the visitor before changing status")
        if requested_status in {"checked_in", "checked_out"} and requested_status != visitor.status:
            raise VisitorError("Use the check-in and check-out actions to change visit status", status_code=422)
    changed = {}
    for field, value in values.items():
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
        note=f"Updated visitor {visitor.full_name}",
    )
    db.commit()
    db.refresh(visitor)
    return visitor


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
    if visitor.status == "checked_in":
        raise VisitorError("Visitor is already checked in")

    visit = VisitorVisit(
        tenant_id=tenant_id,
        visitor_id=visitor.id,
        check_in_time=datetime.now(timezone.utc),
        access_status=access_status,
        notes=notes,
    )
    visitor.status = "checked_in"
    db.add_all([visitor, visit])
    db.flush()
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_checked_in",
        entity_type="visitor_visit",
        entity_id=visit.id,
        details={"visitor_id": visitor.id, "access_status": access_status},
        note=f"Checked in visitor {visitor.full_name}",
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
    if visitor.status != "checked_in":
        raise VisitorError("Visitor is not currently checked in")
    visit = (
        db.query(VisitorVisit)
        .filter(
            VisitorVisit.tenant_id == tenant_id,
            VisitorVisit.visitor_id == visitor.id,
            VisitorVisit.check_out_time.is_(None),
        )
        .order_by(VisitorVisit.check_in_time.desc())
        .first()
    )
    if visit is None:
        raise VisitorError("Active visitor visit was not found")

    visit.check_out_time = datetime.now(timezone.utc)
    if notes:
        visit.notes = f"{visit.notes}\n{notes}" if visit.notes else notes
    visitor.status = "checked_out"
    db.add_all([visitor, visit])
    add_tenant_audit(
        db,
        tenant_id=tenant_id,
        tenant_member_id=actor_id,
        action="visitor_checked_out",
        entity_type="visitor_visit",
        entity_id=visit.id,
        details={"visitor_id": visitor.id},
        note=f"Checked out visitor {visitor.full_name}",
    )
    db.commit()
    db.refresh(visitor)
    db.refresh(visit)
    return visitor, visit

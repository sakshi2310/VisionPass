"""Audit service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember


def add_tenant_audit(
    db: Session,
    *,
    tenant_id: str,
    tenant_member_id: str,
    action: str,
    entity_type: str,
    entity_id: str | None,
    details: dict | None = None,
    note: str | None = None,
) -> AuditLog:
    """Stage an audit record so it commits atomically with the domain change."""

    audit = AuditLog(
        tenant_id=tenant_id,
        tenant_member_id=tenant_member_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        note=note,
    )
    db.add(audit)
    return audit


def log_recognition_attempt(
    db: Session,
    *,
    tenant_id: str,
    tenant_member_id: str,
    result: dict,
    camera_id: str | None,
    mode: str,
) -> AuditLog:
    """Persist one tenant-scoped recognition attempt."""

    audit = AuditLog(
        tenant_id=tenant_id,
        tenant_member_id=tenant_member_id,
        action="face_recognition_attempt",
        entity_type="employee_face_recognition",
        entity_id=result.get("employee_id"),
        details={
            "recognized": bool(result.get("recognized", False)),
            "recognition_status": result.get("recognition_status"),
            "employee_id": result.get("employee_id"),
            "camera_id": camera_id,
            "mode": mode,
            "confidence": result.get("confidence"),
            "distance": result.get("distance"),
            "threshold": result.get("threshold"),
        },
        note=f"Face recognition result: {result.get('recognition_status', 'UNKNOWN')}",
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit


def list_admin_audit_logs(db: Session, limit: int = 100) -> list[dict]:
    super_admin_names = {row.id: row.full_name for row in db.query(SuperAdmin.id, SuperAdmin.full_name).all()}
    member_names = {row.id: row.full_name for row in db.query(TenantMember.id, TenantMember.full_name).all()}
    tenant_names = {row.id: row.name for row in db.query(Tenant.id, Tenant.name).all()}

    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    logs: list[dict] = []
    for row in rows:
        actor = "System"
        if row.super_admin_id is not None:
            actor = super_admin_names.get(row.super_admin_id, "Super Admin")
        elif row.tenant_member_id is not None:
            actor = member_names.get(row.tenant_member_id, "Tenant User")

        logs.append(
            {
                "id": row.id,
                "user": actor,
                "action": row.action,
                "entity": tenant_names.get(row.tenant_id, row.entity_type),
                "entity_id": row.entity_id,
                "note": row.note,
                "details": row.details,
                "timestamp": row.created_at,
            }
        )
    return logs

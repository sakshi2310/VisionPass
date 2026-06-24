"""Audit service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember


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

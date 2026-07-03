"""Audit log model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    super_admin_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("super_admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_member_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenant_members.id", ondelete="SET NULL"),
        nullable=True,
    )
    tenant_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(150), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

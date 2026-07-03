"""Tenant access decision log model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AccessLog(Base):
    __tablename__ = "access_logs"
    __table_args__ = (
        Index("ix_access_logs_tenant_created", "tenant_id", "created_at"),
        Index("ix_access_logs_tenant_decision", "tenant_id", "decision"),
        CheckConstraint(
            "decision IN ('granted', 'denied', 'manual_review')",
            name="ck_access_logs_decision",
        ),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    visitor_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("visitors.id", ondelete="SET NULL"),
        nullable=True,
    )
    camera_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("cameras.id", ondelete="SET NULL"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

"""Tenant visitor registration and visit history models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Visitor(Base):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("ix_visitors_tenant_id", "tenant_id"),
        Index("ix_visitors_tenant_status", "tenant_id", "status"),
        CheckConstraint(
            "status IN ('expected', 'checked_in', 'checked_out', 'blocked')",
            name="ck_visitors_status",
        ),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    host_employee_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    photo_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="expected", server_default=text("'expected'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class VisitorVisit(Base):
    __tablename__ = "visitor_visits"
    __table_args__ = (
        Index("ix_visitor_visits_tenant_visitor", "tenant_id", "visitor_id"),
        Index("ix_visitor_visits_tenant_check_in", "tenant_id", "check_in_time"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    visitor_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("visitors.id", ondelete="CASCADE"),
        nullable=False,
    )
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_status: Mapped[str] = mapped_column(String(50), nullable=False, default="granted", server_default=text("'granted'"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

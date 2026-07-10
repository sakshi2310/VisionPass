"""Tenant visitor registration and visit history models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.vector import Vector


class Visitor(Base):
    __tablename__ = "visitors"
    __table_args__ = (
        Index("ix_visitors_tenant_id", "tenant_id"),
        Index("ix_visitors_tenant_status", "tenant_id", "status"),
        Index("ix_visitors_tenant_last_seen", "tenant_id", "last_seen_at"),
        CheckConstraint(
            "status IN ('active', 'important', 'blocked', 'expected', 'checked_in', 'checked_out')",
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
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    purpose: Mapped[str | None] = mapped_column(Text, nullable=True)
    photo_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    face_embedding: Mapped[list[float] | None] = mapped_column(Vector(512), nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_visits: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default=text("'active'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def name(self) -> str:
        return self.full_name

    @name.setter
    def name(self, value: str) -> None:
        self.full_name = value

    @property
    def image_path(self) -> str | None:
        return self.photo_path

    @image_path.setter
    def image_path(self, value: str | None) -> None:
        self.photo_path = value

    @property
    def photo_url(self) -> str | None:
        return self.photo_path

    @photo_url.setter
    def photo_url(self, value: str | None) -> None:
        self.photo_path = value


class VisitorVisit(Base):
    __tablename__ = "visitor_visits"
    __table_args__ = (
        Index("ix_visitor_visits_tenant_visitor", "tenant_id", "visitor_id"),
        Index("ix_visitor_visits_tenant_seen_at", "tenant_id", "seen_at"),
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
    person_detection_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("person_detections.id", ondelete="SET NULL"),
        nullable=True,
    )
    camera_id: Mapped[str | None] = mapped_column(PGUUID(as_uuid=False), ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True)
    zone_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    check_in_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    access_status: Mapped[str] = mapped_column(String(50), nullable=False, default="granted", server_default=text("'granted'"))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    @property
    def snapshot_url(self) -> str | None:
        return self.image_path

    @snapshot_url.setter
    def snapshot_url(self, value: str | None) -> None:
        self.image_path = value

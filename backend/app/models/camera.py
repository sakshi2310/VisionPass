"""Tenant camera model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Camera(Base):
    __tablename__ = "cameras"
    __table_args__ = (
        Index("ix_cameras_tenant_id", "tenant_id"),
        Index("ix_cameras_tenant_active", "tenant_id", "is_active"),
        CheckConstraint(
            "camera_type IN ('ip_webcam', 'rtsp', 'webcam', 'manual')",
            name="ck_cameras_type",
        ),
        CheckConstraint(
            "health_status IN ('online', 'offline', 'error', 'unknown')",
            name="ck_cameras_health",
        ),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    camera_type: Mapped[str] = mapped_column(String(30), nullable=False)
    stream_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    snapshot_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    password_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    health_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", server_default=text("'unknown'"))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class CameraEvent(Base):
    __tablename__ = "camera_events"
    __table_args__ = (
        Index("ix_camera_events_tenant_camera_time", "tenant_id", "camera_id", "created_at"),
        Index("ix_camera_events_tenant_time", "tenant_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    camera_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    employee_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    recognition_status: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

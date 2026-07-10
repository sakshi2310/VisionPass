"""Person detection records generated from camera frames."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.vector import Vector


class PersonDetection(Base):
    __tablename__ = "person_detections"
    __table_args__ = (
        Index("ix_person_detections_tenant_id", "tenant_id"),
        Index("ix_person_detections_tenant_detected_at", "tenant_id", "detected_at"),
        Index("ix_person_detections_tenant_camera_detected_at", "tenant_id", "camera_id", "detected_at"),
        CheckConstraint(
            "match_type IN ('staff', 'visitor', 'unknown')",
            name="ck_person_detections_match_type",
        ),
        CheckConstraint(
            "status IN ('new', 'reviewed', 'suspicious', 'converted_to_visitor', 'converted_to_staff', 'ignored')",
            name="ck_person_detections_status",
        ),
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
    zone_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    seen_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default=text("1"))
    snapshot_quality_score: Mapped[float | None] = mapped_column(nullable=True)
    face_embedding: Mapped[list[float] | None] = mapped_column(Vector(512), nullable=True)
    match_type: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown", server_default=text("'unknown'"))
    matched_staff_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    matched_visitor_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("visitors.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="new", server_default=text("'new'"))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

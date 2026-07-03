"""Employee and face enrollment models."""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.vector import Vector


class AttendanceEmployee(Base):
    __tablename__ = "attendance_employees"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_code", name="uq_attendance_employees_tenant_code"),
        UniqueConstraint("tenant_id", "email", name="uq_attendance_employees_tenant_email"),
        Index("ix_attendance_employees_tenant_id", "tenant_id"),
        Index("ix_attendance_employees_shift_id", "shift_id"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_code: Mapped[str] = mapped_column(String(100), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    designation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    shift_id: Mapped[str | None] = mapped_column(PGUUID(as_uuid=False), ForeignKey("attendance_shifts.id", ondelete="SET NULL"), nullable=True)
    joining_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    employee_type: Mapped[str] = mapped_column(String(50), nullable=False, default="Full Time", server_default=text("'Full Time'"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmployeeFaceProfile(Base):
    __tablename__ = "employee_face_profiles"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_id", name="uq_employee_face_profiles_tenant_employee"),
        Index("ix_employee_face_profiles_tenant_id", "tenant_id"),
        Index("ix_employee_face_profiles_employee_id", "employee_id"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False)
    enrollment_status: Mapped[str] = mapped_column(String(50), nullable=False, default="Not Enrolled", server_default=text("'Not Enrolled'"))
    face_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    embedding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    average_quality_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    last_enrolled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class EmployeeFaceImage(Base):
    __tablename__ = "employee_face_images"
    __table_args__ = (
        Index("ix_employee_face_images_tenant_id", "tenant_id"),
        Index("ix_employee_face_images_employee_id", "employee_id"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False)
    image_url: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    face_detected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    face_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    validation_status: Mapped[str] = mapped_column(String(50), nullable=False, default="Pending", server_default=text("'Pending'"))
    validation_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class EmployeeFaceEmbedding(Base):
    __tablename__ = "employee_face_embeddings"
    __table_args__ = (
        Index("ix_employee_face_embeddings_tenant_id", "tenant_id"),
        Index("ix_employee_face_embeddings_employee_id", "employee_id"),
        Index("ix_employee_face_embeddings_face_image_id", "face_image_id"),
        Index(
            "idx_employee_face_embeddings_vector",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    employee_id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False)
    face_image_id: Mapped[str | None] = mapped_column(PGUUID(as_uuid=False), ForeignKey("employee_face_images.id", ondelete="SET NULL"), nullable=True)
    embedding: Mapped[list[float]] = mapped_column(Vector(512), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    quality_score: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

"""Attendance configuration models."""

from __future__ import annotations

from datetime import date, datetime, time

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Time, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AttendanceShift(Base):
    __tablename__ = "attendance_shifts"
    __table_args__ = (
        Index("ix_attendance_shifts_tenant_id", "tenant_id"),
        Index("ix_attendance_shifts_tenant_default", "tenant_id", "is_default"),
        Index("ix_attendance_shifts_tenant_active", "tenant_id", "is_active"),
        CheckConstraint("grace_period_minutes >= 0", name="ck_attendance_shifts_grace_period_non_negative"),
        CheckConstraint("late_after_minutes >= 0", name="ck_attendance_shifts_late_after_non_negative"),
        CheckConstraint("half_day_min_minutes > 0", name="ck_attendance_shifts_half_day_positive"),
        CheckConstraint("full_day_min_minutes > 0", name="ck_attendance_shifts_full_day_positive"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    start_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    end_time: Mapped[time] = mapped_column(Time(timezone=False), nullable=False)
    grace_period_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    late_after_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    half_day_min_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    full_day_min_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    auto_checkout_time: Mapped[time | None] = mapped_column(Time(timezone=False), nullable=True)
    break_duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AttendanceWorkingDay(Base):
    __tablename__ = "attendance_working_days"
    __table_args__ = (
        UniqueConstraint("tenant_id", "day_of_week", name="uq_attendance_working_days_tenant_day"),
        CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_attendance_working_days_day_of_week"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    is_working: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AttendanceHoliday(Base):
    __tablename__ = "attendance_holidays"
    __table_args__ = (
        UniqueConstraint("tenant_id", "holiday_date", "department_id", "location_id", name="uq_attendance_holidays_scope_date"),
        Index("ix_attendance_holidays_tenant_id", "tenant_id"),
        Index("ix_attendance_holidays_tenant_date", "tenant_id", "holiday_date"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    holiday_name: Mapped[str] = mapped_column(String(255), nullable=False)
    holiday_date: Mapped[date] = mapped_column(Date, nullable=False)
    department_id: Mapped[str | None] = mapped_column(PGUUID(as_uuid=False), nullable=True)
    location_id: Mapped[str | None] = mapped_column(PGUUID(as_uuid=False), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AttendanceSettings(Base):
    __tablename__ = "attendance_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_attendance_settings_tenant"),)

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    duplicate_detection_cooldown_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default=text("5"))
    allow_manual_correction: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    require_correction_reason: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    timezone: Mapped[str] = mapped_column(String(100), nullable=False, default="Asia/Kolkata", server_default=text("'Asia/Kolkata'"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AttendanceFaceSettings(Base):
    __tablename__ = "attendance_face_settings"
    __table_args__ = (UniqueConstraint("tenant_id", name="uq_attendance_face_settings_tenant"),)

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    face_match_threshold: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.65, server_default=text("0.65"))
    min_face_images: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default=text("3"))
    recommended_face_images: Mapped[int] = mapped_column(Integer, nullable=False, default=5, server_default=text("5"))
    max_face_images: Mapped[int] = mapped_column(Integer, nullable=False, default=10, server_default=text("10"))
    min_face_size_px: Mapped[int] = mapped_column(Integer, nullable=False, default=64, server_default=text("64"))
    min_resolution_width: Mapped[int] = mapped_column(Integer, nullable=False, default=320, server_default=text("320"))
    min_resolution_height: Mapped[int] = mapped_column(Integer, nullable=False, default=240, server_default=text("240"))
    max_blur_score: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=120.0, server_default=text("120.0"))
    min_brightness: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=35.0, server_default=text("35.0"))
    max_brightness: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=220.0, server_default=text("220.0"))
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="buffalo_l", server_default=text("'buffalo_l'")
    )
    embedding_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    embedding_dimension: Mapped[int] = mapped_column(Integer, nullable=False, default=512, server_default=text("512"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"
    __table_args__ = (
        Index("ix_attendance_events_tenant_employee_time", "tenant_id", "employee_id", "event_time"),
        Index("ix_attendance_events_tenant_time", "tenant_id", "event_time"),
        CheckConstraint("event_type IN ('check_in', 'check_out')", name="ck_attendance_events_type"),
        CheckConstraint("source IN ('camera', 'manual', 'web')", name="ck_attendance_events_source"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    camera_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(7, 6), nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DailyAttendanceRecord(Base):
    __tablename__ = "daily_attendance_records"
    __table_args__ = (
        UniqueConstraint("tenant_id", "employee_id", "attendance_date", name="uq_daily_attendance_tenant_employee_date"),
        Index("ix_daily_attendance_tenant_date", "tenant_id", "attendance_date"),
        CheckConstraint(
            "status IN ('present', 'late', 'half_day', 'absent', 'holiday')",
            name="ck_daily_attendance_status",
        ),
        CheckConstraint("total_work_minutes >= 0", name="ck_daily_attendance_work_non_negative"),
    )

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False)
    first_check_in: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_check_out: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    total_work_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="absent", server_default=text("'absent'"))
    shift_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("attendance_shifts.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

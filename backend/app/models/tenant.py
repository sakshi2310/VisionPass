"""Tenant model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import account_status_enum


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    logo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(account_status_enum, nullable=False, default="active")
    industry: Mapped[str] = mapped_column(String(100), nullable=False, default="General")
    plan: Mapped[str] = mapped_column(String(50), nullable=False, default="basic")
    max_users: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    max_devices: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

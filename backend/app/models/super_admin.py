"""Super admin model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import account_status_enum


class SuperAdmin(Base):
    __tablename__ = "super_admins"

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(account_status_enum, nullable=False, default="active")
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def role(self) -> str:
        return "super_admin"

    @property
    def tenant_id(self) -> None:
        return None

    @property
    def phone(self) -> None:
        return None

    @property
    def department(self) -> None:
        return None

    @property
    def designation(self) -> None:
        return None

    @property
    def employee_id(self) -> None:
        return None

    @property
    def access_zones(self) -> list[str]:
        return []

    @property
    def face_enrolled(self) -> bool:
        return False

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_deleted(self) -> bool:
        return self.status != "active"

    @property
    def notes(self) -> None:
        return None

    @property
    def created_by(self) -> None:
        return None

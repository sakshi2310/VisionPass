"""Tenant feature assignment model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TenantFeature(Base):
    __tablename__ = "tenant_features"
    __table_args__ = (UniqueConstraint("tenant_id", "feature_code", name="uq_tenant_features_tenant_code"),)

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    feature_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_by_super_admin_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("super_admins.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by_member_id: Mapped[str | None] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenant_members.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    @property
    def module_name(self) -> str:
        return self.feature_code

    @module_name.setter
    def module_name(self, value: str) -> None:
        self.feature_code = value

    @property
    def updated_by(self) -> str | None:
        return self.updated_by_member_id or self.updated_by_super_admin_id

    @updated_by.setter
    def updated_by(self, value: str | None) -> None:
        self.updated_by_member_id = value
        self.updated_by_super_admin_id = None

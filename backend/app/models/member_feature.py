"""Member feature override model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MemberFeature(Base):
    __tablename__ = "member_features"
    __table_args__ = (UniqueConstraint("tenant_member_id", "feature_code", name="uq_member_features_member_code"),)

    id: Mapped[str] = mapped_column(PGUUID(as_uuid=False), primary_key=True, server_default=text("gen_random_uuid()"))
    tenant_member_id: Mapped[str] = mapped_column(
        PGUUID(as_uuid=False),
        ForeignKey("tenant_members.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_code: Mapped[str] = mapped_column(String(100), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

"""Add attendance configuration tables.

Revision ID: 0003_add_attendance_module
Revises: 0002_add_tenant_address
Create Date: 2026-06-24 00:00:02.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0003_add_attendance_module"
down_revision = "0002_add_tenant_address"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("duplicate_detection_cooldown_minutes", sa.Integer(), nullable=False, server_default=sa.text("5")),
        sa.Column("allow_manual_correction", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("require_correction_reason", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("timezone", sa.String(length=100), nullable=False, server_default=sa.text("'Asia/Kolkata'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", name="uq_attendance_settings_tenant"),
    )

    op.create_table(
        "attendance_working_days",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("is_working", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "day_of_week", name="uq_attendance_working_days_tenant_day"),
        sa.CheckConstraint("day_of_week >= 0 AND day_of_week <= 6", name="ck_attendance_working_days_day_of_week"),
    )

    op.create_table(
        "attendance_shifts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("grace_period_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("late_after_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("half_day_min_minutes", sa.Integer(), nullable=False),
        sa.Column("full_day_min_minutes", sa.Integer(), nullable=False),
        sa.Column("auto_checkout_time", sa.Time(), nullable=True),
        sa.Column("break_duration_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("grace_period_minutes >= 0", name="ck_attendance_shifts_grace_period_non_negative"),
        sa.CheckConstraint("late_after_minutes >= 0", name="ck_attendance_shifts_late_after_non_negative"),
        sa.CheckConstraint("half_day_min_minutes > 0", name="ck_attendance_shifts_half_day_positive"),
        sa.CheckConstraint("full_day_min_minutes > 0", name="ck_attendance_shifts_full_day_positive"),
    )
    op.create_index("ix_attendance_shifts_tenant_id", "attendance_shifts", ["tenant_id"])
    op.create_index("ix_attendance_shifts_tenant_default", "attendance_shifts", ["tenant_id", "is_default"])
    op.create_index("ix_attendance_shifts_tenant_active", "attendance_shifts", ["tenant_id", "is_active"])

    op.create_table(
        "attendance_holidays",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("holiday_name", sa.String(length=255), nullable=False),
        sa.Column("holiday_date", sa.Date(), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "holiday_date", "department_id", "location_id", name="uq_attendance_holidays_scope_date"),
    )
    op.create_index("ix_attendance_holidays_tenant_id", "attendance_holidays", ["tenant_id"])
    op.create_index("ix_attendance_holidays_tenant_date", "attendance_holidays", ["tenant_id", "holiday_date"])


def downgrade() -> None:
    op.drop_index("ix_attendance_holidays_tenant_date", table_name="attendance_holidays")
    op.drop_index("ix_attendance_holidays_tenant_id", table_name="attendance_holidays")
    op.drop_table("attendance_holidays")

    op.drop_index("ix_attendance_shifts_tenant_active", table_name="attendance_shifts")
    op.drop_index("ix_attendance_shifts_tenant_default", table_name="attendance_shifts")
    op.drop_index("ix_attendance_shifts_tenant_id", table_name="attendance_shifts")
    op.drop_table("attendance_shifts")

    op.drop_table("attendance_working_days")
    op.drop_table("attendance_settings")

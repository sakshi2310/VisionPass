"""Add attendance events and daily attendance records."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0006_add_attendance_tracking"
down_revision = "0005_retire_face_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column("camera_id", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Numeric(7, 6), nullable=True),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("event_type IN ('check_in', 'check_out')", name="ck_attendance_events_type"),
        sa.CheckConstraint("source IN ('camera', 'manual', 'web')", name="ck_attendance_events_source"),
    )
    op.create_index(
        "ix_attendance_events_tenant_employee_time",
        "attendance_events",
        ["tenant_id", "employee_id", "event_time"],
    )
    op.create_index("ix_attendance_events_tenant_time", "attendance_events", ["tenant_id", "event_time"])

    op.create_table(
        "daily_attendance_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("first_check_in", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_check_out", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_work_minutes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'absent'")),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "employee_id", "attendance_date", name="uq_daily_attendance_tenant_employee_date"),
        sa.CheckConstraint(
            "status IN ('present', 'late', 'half_day', 'absent', 'holiday')",
            name="ck_daily_attendance_status",
        ),
        sa.CheckConstraint("total_work_minutes >= 0", name="ck_daily_attendance_work_non_negative"),
    )
    op.create_index(
        "ix_daily_attendance_tenant_date",
        "daily_attendance_records",
        ["tenant_id", "attendance_date"],
    )


def downgrade() -> None:
    op.drop_index("ix_daily_attendance_tenant_date", table_name="daily_attendance_records")
    op.drop_table("daily_attendance_records")
    op.drop_index("ix_attendance_events_tenant_time", table_name="attendance_events")
    op.drop_index("ix_attendance_events_tenant_employee_time", table_name="attendance_events")
    op.drop_table("attendance_events")

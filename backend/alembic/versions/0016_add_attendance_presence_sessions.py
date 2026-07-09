"""Add persisted attendance presence sessions.

Revision ID: 0016_attendance_sessions
Revises: 0015_camera_detection_zones
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0016_attendance_sessions"
down_revision = "0015_camera_detection_zones"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attendance_presence_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=False), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column(
            "employee_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("session_type", sa.String(length=20), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("latest_source", sa.String(length=20), nullable=True),
        sa.Column(
            "camera_id",
            postgresql.UUID(as_uuid=False),
            sa.ForeignKey("cameras.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("session_type IN ('present', 'absent')", name="ck_attendance_presence_sessions_type"),
    )
    op.create_index(
        "ix_attendance_presence_sessions_tenant_employee_date",
        "attendance_presence_sessions",
        ["tenant_id", "employee_id", "attendance_date"],
    )
    op.create_index(
        "ix_attendance_presence_sessions_tenant_employee_start",
        "attendance_presence_sessions",
        ["tenant_id", "employee_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_attendance_presence_sessions_tenant_employee_start", table_name="attendance_presence_sessions")
    op.drop_index("ix_attendance_presence_sessions_tenant_employee_date", table_name="attendance_presence_sessions")
    op.drop_table("attendance_presence_sessions")

"""Add tenant camera processing event logs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_add_camera_events"
down_revision = "0007_add_cameras"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "camera_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("recognition_status", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index(
        "ix_camera_events_tenant_camera_time",
        "camera_events",
        ["tenant_id", "camera_id", "created_at"],
    )
    op.create_index("ix_camera_events_tenant_time", "camera_events", ["tenant_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_camera_events_tenant_time", table_name="camera_events")
    op.drop_index("ix_camera_events_tenant_camera_time", table_name="camera_events")
    op.drop_table("camera_events")

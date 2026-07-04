"""Add tenant camera management."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_add_cameras"
down_revision = "0006_add_attendance_tracking"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("camera_type", sa.String(length=30), nullable=False),
        sa.Column("stream_url", sa.Text(), nullable=True),
        sa.Column("snapshot_url", sa.Text(), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("password_encrypted", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("health_status", sa.String(length=20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "camera_type IN ('ip_webcam', 'rtsp', 'webcam', 'manual')",
            name="ck_cameras_type",
        ),
        sa.CheckConstraint(
            "health_status IN ('online', 'offline', 'error', 'unknown')",
            name="ck_cameras_health",
        ),
    )
    op.create_index("ix_cameras_tenant_id", "cameras", ["tenant_id"])
    op.create_index("ix_cameras_tenant_active", "cameras", ["tenant_id", "is_active"])


def downgrade() -> None:
    op.drop_index("ix_cameras_tenant_active", table_name="cameras")
    op.drop_index("ix_cameras_tenant_id", table_name="cameras")
    op.drop_table("cameras")

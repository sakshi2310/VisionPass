"""Extend camera sources for phone IP webcams and feature assignment."""

from alembic import op
import sqlalchemy as sa


revision = "0013_extend_camera_sources"
down_revision = "0012_add_tenant_company_email"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_cameras_type", "cameras", type_="check")
    op.add_column("cameras", sa.Column("phone_ip", sa.String(length=255), nullable=True))
    op.add_column("cameras", sa.Column("port", sa.Integer(), nullable=True))
    op.add_column(
        "cameras",
        sa.Column(
            "assigned_feature_scope",
            sa.String(length=30),
            nullable=False,
            server_default=sa.text("'both'"),
        ),
    )
    op.create_check_constraint(
        "ck_cameras_type",
        "cameras",
        "camera_type IN ('ip_webcam', 'phone_ip_webcam', 'rtsp', 'http_mjpeg', 'webcam', 'manual', 'manual_snapshot')",
    )
    op.create_check_constraint(
        "ck_cameras_feature_scope",
        "cameras",
        "assigned_feature_scope IN ('attendance', 'object_detection', 'both')",
    )


def downgrade() -> None:
    op.execute("UPDATE cameras SET camera_type = 'ip_webcam' WHERE camera_type = 'phone_ip_webcam'")
    op.execute("UPDATE cameras SET camera_type = 'manual' WHERE camera_type IN ('http_mjpeg', 'manual_snapshot')")
    op.drop_constraint("ck_cameras_feature_scope", "cameras", type_="check")
    op.drop_constraint("ck_cameras_type", "cameras", type_="check")
    op.drop_column("cameras", "assigned_feature_scope")
    op.drop_column("cameras", "port")
    op.drop_column("cameras", "phone_ip")
    op.create_check_constraint(
        "ck_cameras_type",
        "cameras",
        "camera_type IN ('ip_webcam', 'rtsp', 'webcam', 'manual')",
    )

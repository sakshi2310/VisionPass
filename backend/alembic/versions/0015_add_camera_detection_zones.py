"""Add persisted object-detection zones to cameras.

Revision ID: 0015_camera_detection_zones
Revises: 0014_feature_delete_tombstone
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0015_camera_detection_zones"
down_revision = "0014_feature_delete_tombstone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cameras",
        sa.Column(
            "detection_zones",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
    )


def downgrade() -> None:
    op.drop_column("cameras", "detection_zones")

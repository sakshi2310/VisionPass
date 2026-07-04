"""Add a deletion tombstone to master features.

Revision ID: 0014_feature_delete_tombstone
Revises: 0013_extend_camera_sources
"""

from alembic import op
import sqlalchemy as sa


revision = "0014_feature_delete_tombstone"
down_revision = "0013_extend_camera_sources"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "features",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("features", "is_deleted")

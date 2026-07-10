"""Add person detection dedupe tracking fields.

Revision ID: 0020_add_person_detection_dedupe_fields
Revises: 0019_add_suspicious_person_detection_status
"""

from alembic import op
import sqlalchemy as sa


revision = "0020_add_person_detection_dedupe_fields"
down_revision = "0019_add_suspicious_person_detection_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("person_detections", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("person_detections", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "person_detections",
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
    )
    op.add_column("person_detections", sa.Column("snapshot_quality_score", sa.Float(), nullable=True))

    op.execute(
        """
        UPDATE person_detections
        SET
            first_seen_at = COALESCE(first_seen_at, detected_at),
            last_seen_at = COALESCE(last_seen_at, detected_at),
            seen_count = COALESCE(seen_count, 1)
        """
    )

    op.drop_constraint("ck_person_detections_status", "person_detections", type_="check")
    op.create_check_constraint(
        "ck_person_detections_status",
        "person_detections",
        "status IN ('new', 'reviewed', 'suspicious', 'converted_to_visitor', 'converted_to_staff', 'ignored')",
    )
    op.alter_column("person_detections", "first_seen_at", nullable=False)
    op.alter_column("person_detections", "last_seen_at", nullable=False)


def downgrade() -> None:
    op.drop_constraint("ck_person_detections_status", "person_detections", type_="check")
    op.create_check_constraint(
        "ck_person_detections_status",
        "person_detections",
        "status IN ('new', 'reviewed', 'suspicious', 'converted_to_visitor', 'ignored')",
    )
    op.drop_column("person_detections", "snapshot_quality_score")
    op.drop_column("person_detections", "seen_count")
    op.drop_column("person_detections", "last_seen_at")
    op.drop_column("person_detections", "first_seen_at")

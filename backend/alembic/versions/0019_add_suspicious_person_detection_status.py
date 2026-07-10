"""Allow suspicious person detection review state.

Revision ID: 0019_add_suspicious_person_detection_status
Revises: 0018_update_visitors_for_person_detection
"""

from alembic import op
import sqlalchemy as sa


revision = "0019_add_suspicious_person_detection_status"
down_revision = "0018_update_visitors_for_person_detection"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_person_detections_status", "person_detections", type_="check")
    op.create_check_constraint(
        "ck_person_detections_status",
        "person_detections",
        "status IN ('new', 'reviewed', 'suspicious', 'converted_to_visitor', 'ignored')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_person_detections_status", "person_detections", type_="check")
    op.create_check_constraint(
        "ck_person_detections_status",
        "person_detections",
        "status IN ('new', 'reviewed', 'converted_to_visitor', 'ignored')",
    )

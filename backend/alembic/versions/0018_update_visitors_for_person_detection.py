"""Update visitor tables for person detection conversions.

Revision ID: 0018_update_visitors_for_person_detection
Revises: 0017_add_person_detections
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision = "0018_update_visitors_for_person_detection"
down_revision = "0017_add_person_detections"
branch_labels = None
depends_on = None


class Vector(UserDefinedType):
    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"VECTOR({self.dimensions})"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column("visitors", sa.Column("face_embedding", Vector(512), nullable=True))
    op.add_column("visitors", sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("visitors", sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("visitors", sa.Column("total_visits", sa.Integer(), nullable=False, server_default=sa.text("0")))
    op.add_column("visitors", sa.Column("notes", sa.Text(), nullable=True))

    op.alter_column("visitors", "phone", existing_type=sa.String(length=50), nullable=True)
    op.alter_column("visitors", "purpose", existing_type=sa.Text(), nullable=True)
    op.alter_column("visitors", "status", existing_type=sa.String(length=20), server_default=sa.text("'active'"))

    op.execute(
        """
        UPDATE visitors
        SET total_visits = COALESCE(visit_counts.visit_count, 0),
            first_seen_at = visit_counts.first_seen_at,
            last_seen_at = visit_counts.last_seen_at
        FROM (
            SELECT
                visitor_id,
                COUNT(*) AS visit_count,
                MIN(check_in_time) AS first_seen_at,
                MAX(COALESCE(check_out_time, check_in_time)) AS last_seen_at
            FROM visitor_visits
            GROUP BY visitor_id
        ) AS visit_counts
        WHERE visitors.id = visit_counts.visitor_id
        """
    )

    op.execute(
        """
        UPDATE visitors
        SET total_visits = 0
        WHERE total_visits IS NULL
        """
    )

    op.add_column("visitor_visits", sa.Column("person_detection_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("person_detections.id", ondelete="SET NULL"), nullable=True))
    op.add_column("visitor_visits", sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True))
    op.add_column("visitor_visits", sa.Column("zone_id", sa.String(length=100), nullable=True))
    op.add_column("visitor_visits", sa.Column("seen_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("visitor_visits", sa.Column("image_path", sa.Text(), nullable=True))

    op.execute(
        """
        UPDATE visitor_visits
        SET seen_at = COALESCE(check_in_time, created_at),
            image_path = NULL
        WHERE seen_at IS NULL
        """
    )

    op.alter_column("visitor_visits", "seen_at", existing_type=sa.DateTime(timezone=True), nullable=False)
    op.create_index("ix_visitors_tenant_last_seen", "visitors", ["tenant_id", "last_seen_at"])
    op.create_index("ix_visitor_visits_tenant_seen_at", "visitor_visits", ["tenant_id", "seen_at"])

    op.drop_constraint("ck_visitors_status", "visitors", type_="check")
    op.create_check_constraint(
        "ck_visitors_status",
        "visitors",
        "status IN ('active', 'important', 'blocked', 'expected', 'checked_in', 'checked_out')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_visitors_status", "visitors", type_="check")
    op.create_check_constraint(
        "ck_visitors_status",
        "visitors",
        "status IN ('expected', 'checked_in', 'checked_out', 'blocked')",
    )

    op.drop_index("ix_visitor_visits_tenant_seen_at", table_name="visitor_visits")
    op.drop_index("ix_visitors_tenant_last_seen", table_name="visitors")

    op.drop_column("visitor_visits", "image_path")
    op.drop_column("visitor_visits", "seen_at")
    op.drop_column("visitor_visits", "zone_id")
    op.drop_column("visitor_visits", "camera_id")
    op.drop_column("visitor_visits", "person_detection_id")

    op.drop_column("visitors", "notes")
    op.drop_column("visitors", "total_visits")
    op.drop_column("visitors", "last_seen_at")
    op.drop_column("visitors", "first_seen_at")
    op.drop_column("visitors", "face_embedding")

    op.alter_column("visitors", "purpose", existing_type=sa.Text(), nullable=False)
    op.alter_column("visitors", "phone", existing_type=sa.String(length=50), nullable=False)
    op.alter_column("visitors", "status", existing_type=sa.String(length=20), server_default=sa.text("'expected'"))

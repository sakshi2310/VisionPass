"""Add person detections table.

Revision ID: 0017_add_person_detections
Revises: 0016_attendance_sessions
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision = "0017_add_person_detections"
down_revision = "0016_attendance_sessions"
branch_labels = None
depends_on = None


class Vector(UserDefinedType):
    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"VECTOR({self.dimensions})"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "person_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_id", sa.String(length=100), nullable=True),
        sa.Column("image_path", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("face_embedding", Vector(512), nullable=True),
        sa.Column("match_type", sa.String(length=20), nullable=False, server_default=sa.text("'unknown'")),
        sa.Column("matched_staff_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("matched_visitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visitors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default=sa.text("'new'")),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("match_type IN ('staff', 'visitor', 'unknown')", name="ck_person_detections_match_type"),
        sa.CheckConstraint("status IN ('new', 'reviewed', 'converted_to_visitor', 'ignored')", name="ck_person_detections_status"),
    )
    op.create_index("ix_person_detections_tenant_id", "person_detections", ["tenant_id"])
    op.create_index("ix_person_detections_tenant_detected_at", "person_detections", ["tenant_id", "detected_at"])
    op.create_index(
        "ix_person_detections_tenant_camera_detected_at",
        "person_detections",
        ["tenant_id", "camera_id", "detected_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_person_detections_tenant_camera_detected_at", table_name="person_detections")
    op.drop_index("ix_person_detections_tenant_detected_at", table_name="person_detections")
    op.drop_index("ix_person_detections_tenant_id", table_name="person_detections")
    op.drop_table("person_detections")

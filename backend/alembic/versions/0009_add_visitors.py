"""Add tenant visitor registration and visit history."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0009_add_visitors"
down_revision = "0008_add_camera_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "visitors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("company", sa.String(length=255), nullable=True),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("host_employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("photo_path", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'expected'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "status IN ('expected', 'checked_in', 'checked_out', 'blocked')",
            name="ck_visitors_status",
        ),
    )
    op.create_index("ix_visitors_tenant_id", "visitors", ["tenant_id"])
    op.create_index("ix_visitors_tenant_status", "visitors", ["tenant_id", "status"])

    op.create_table(
        "visitor_visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visitors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("check_in_time", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("check_out_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("access_status", sa.String(length=50), nullable=False, server_default=sa.text("'granted'")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_visitor_visits_tenant_visitor", "visitor_visits", ["tenant_id", "visitor_id"])
    op.create_index("ix_visitor_visits_tenant_check_in", "visitor_visits", ["tenant_id", "check_in_time"])


def downgrade() -> None:
    op.drop_index("ix_visitor_visits_tenant_check_in", table_name="visitor_visits")
    op.drop_index("ix_visitor_visits_tenant_visitor", table_name="visitor_visits")
    op.drop_table("visitor_visits")
    op.drop_index("ix_visitors_tenant_status", table_name="visitors")
    op.drop_index("ix_visitors_tenant_id", table_name="visitors")
    op.drop_table("visitors")

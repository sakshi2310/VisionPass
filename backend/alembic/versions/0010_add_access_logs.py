"""Add tenant access decision logs."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0010_add_access_logs"
down_revision = "0009_add_visitors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "access_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("visitor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("visitors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "decision IN ('granted', 'denied', 'manual_review')",
            name="ck_access_logs_decision",
        ),
    )
    op.create_index("ix_access_logs_tenant_created", "access_logs", ["tenant_id", "created_at"])
    op.create_index("ix_access_logs_tenant_decision", "access_logs", ["tenant_id", "decision"])


def downgrade() -> None:
    op.drop_index("ix_access_logs_tenant_decision", table_name="access_logs")
    op.drop_index("ix_access_logs_tenant_created", table_name="access_logs")
    op.drop_table("access_logs")

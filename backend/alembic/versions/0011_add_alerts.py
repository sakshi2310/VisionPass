"""Add tenant security and attendance alerts."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0011_add_alerts"
down_revision = "0010_add_access_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alert_type", sa.String(length=80), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'open'")),
        sa.Column("source_type", sa.String(length=80), nullable=False),
        sa.Column("source_id", sa.String(length=100), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("severity IN ('low', 'medium', 'high', 'critical')", name="ck_alerts_severity"),
        sa.CheckConstraint("status IN ('open', 'acknowledged', 'resolved')", name="ck_alerts_status"),
    )
    op.create_index("ix_alerts_tenant_created", "alerts", ["tenant_id", "created_at"])
    op.create_index("ix_alerts_tenant_status", "alerts", ["tenant_id", "status"])
    op.create_index("ix_alerts_tenant_type", "alerts", ["tenant_id", "alert_type"])


def downgrade() -> None:
    op.drop_index("ix_alerts_tenant_type", table_name="alerts")
    op.drop_index("ix_alerts_tenant_status", table_name="alerts")
    op.drop_index("ix_alerts_tenant_created", table_name="alerts")
    op.drop_table("alerts")

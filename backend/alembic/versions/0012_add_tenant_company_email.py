"""Add a company email separate from the tenant-admin login email.

Revision ID: 0012_add_tenant_company_email
Revises: 0011_add_alerts
"""

from alembic import op
import sqlalchemy as sa


revision = "0012_add_tenant_company_email"
down_revision = "0011_add_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("company_email", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE tenants AS tenant
        SET company_email = (
            SELECT member.email
            FROM tenant_members AS member
            WHERE member.tenant_id = tenant.id
              AND member.role = 'tenant_admin'
              AND member.is_deleted = false
            ORDER BY member.created_at ASC
            LIMIT 1
        )
        WHERE tenant.company_email IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("tenants", "company_email")

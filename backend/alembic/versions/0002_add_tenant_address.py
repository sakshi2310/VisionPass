"""Add tenant address column.

Revision ID: 0002_add_tenant_address
Revises: 0001_clean_visionpass_schema
Create Date: 2026-06-24 00:00:01.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_tenant_address"
down_revision = "0001_clean_visionpass_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tenants", sa.Column("address", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("tenants", "address")

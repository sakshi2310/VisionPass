"""Clean VisionPass SaaS schema.

Revision ID: 0001_clean_visionpass_schema
Revises: 
Create Date: 2026-06-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001_clean_visionpass_schema"
down_revision = None
branch_labels = None
depends_on = None


account_status_enum = postgresql.ENUM(
    "active",
    "inactive",
    "suspended",
    name="account_status",
    create_type=False,
)
member_role_enum = postgresql.ENUM(
    "tenant_admin",
    "user",
    name="member_role",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE account_status AS ENUM ('active', 'inactive', 'suspended');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            CREATE TYPE member_role AS ENUM ('tenant_admin', 'user');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END
        $$;
        """
    )

    for table_name in [
        "auth_sessions",
        "member_features",
        "tenant_features",
        "audit_logs",
        "tenant_members",
        "super_admins",
        "features",
        "tenants",
        "tenant_admins",
        "users",
        "feature_flags",
        "cv_features",
    ]:
        op.execute(sa.text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))

    op.create_table(
        "super_admins",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("status", account_status_enum, nullable=False, server_default=sa.text("'active'")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("logo_url", sa.String(length=255), nullable=True),
        sa.Column("status", account_status_enum, nullable=False, server_default=sa.text("'active'")),
        sa.Column("industry", sa.String(length=100), nullable=False, server_default=sa.text("'General'")),
        sa.Column("plan", sa.String(length=50), nullable=False, server_default=sa.text("'basic'")),
        sa.Column("max_users", sa.Integer(), nullable=False, server_default=sa.text("100")),
        sa.Column("max_devices", sa.Integer(), nullable=False, server_default=sa.text("20")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("feature_name", sa.String(length=255), nullable=False),
        sa.Column("feature_code", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", account_status_enum, nullable=False, server_default=sa.text("'active'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "tenant_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("role", member_role_enum, nullable=False, server_default=sa.text("'user'")),
        sa.Column("status", account_status_enum, nullable=False, server_default=sa.text("'active'")),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.Column("employee_id", sa.String(length=100), nullable=True),
        sa.Column("access_zones", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("face_enrolled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_tenant_members_tenant_email"),
    )

    op.create_table(
        "tenant_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_by_super_admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("super_admins.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_by_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "feature_code", name="uq_tenant_features_tenant_code"),
    )

    op.create_table(
        "member_features",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_members.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_code", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_member_id", "feature_code", name="uq_member_features_member_code"),
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("super_admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("super_admins.id", ondelete="CASCADE"), nullable=True),
        sa.Column("tenant_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_members.id", ondelete="CASCADE"), nullable=True),
        sa.Column("access_token_hash", sa.String(length=255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint(
            "((super_admin_id IS NOT NULL)::int + (tenant_member_id IS NOT NULL)::int) = 1",
            name="ck_auth_sessions_one_principal",
        ),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("super_admin_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("super_admins.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_member_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenant_members.id", ondelete="SET NULL"), nullable=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=True),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    for table_name in [
        "audit_logs",
        "auth_sessions",
        "member_features",
        "tenant_features",
        "tenant_members",
        "features",
        "tenants",
        "super_admins",
    ]:
        op.drop_table(table_name)

    op.execute("DROP TYPE IF EXISTS member_role")
    op.execute("DROP TYPE IF EXISTS account_status")

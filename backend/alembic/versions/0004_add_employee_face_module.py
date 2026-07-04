"""Add employee and face enrollment tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import UserDefinedType


revision = "0004_add_employee_face_module"
down_revision = "0003_add_attendance_module"
branch_labels = None
depends_on = None


class Vector(UserDefinedType):
    def __init__(self, dimensions: int):
        self.dimensions = dimensions

    def get_col_spec(self, **kw):
        return f"VECTOR({self.dimensions})"


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = set(inspector.get_table_names())

    if "attendance_face_settings" not in existing_tables:
        op.create_table(
            "attendance_face_settings",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
            sa.Column("face_match_threshold", sa.Numeric(5, 4), nullable=False, server_default=sa.text("0.65")),
            sa.Column("min_face_images", sa.Integer(), nullable=False, server_default=sa.text("3")),
            sa.Column("recommended_face_images", sa.Integer(), nullable=False, server_default=sa.text("5")),
            sa.Column("max_face_images", sa.Integer(), nullable=False, server_default=sa.text("10")),
            sa.Column("min_face_size_px", sa.Integer(), nullable=False, server_default=sa.text("64")),
            sa.Column("min_resolution_width", sa.Integer(), nullable=False, server_default=sa.text("320")),
            sa.Column("min_resolution_height", sa.Integer(), nullable=False, server_default=sa.text("240")),
            sa.Column("max_blur_score", sa.Numeric(10, 4), nullable=False, server_default=sa.text("120.0")),
            sa.Column("min_brightness", sa.Numeric(10, 4), nullable=False, server_default=sa.text("35.0")),
            sa.Column("max_brightness", sa.Numeric(10, 4), nullable=False, server_default=sa.text("220.0")),
            sa.Column("embedding_model", sa.String(length=100), nullable=False, server_default=sa.text("'buffalo_l'")),
            sa.Column("embedding_version", sa.String(length=50), nullable=True),
            sa.Column("embedding_dimension", sa.Integer(), nullable=False, server_default=sa.text("512")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
            sa.UniqueConstraint("tenant_id", name="uq_attendance_face_settings_tenant"),
        )
    else:
        index_names = {index["name"] for index in inspector.get_indexes("attendance_face_settings")}
        if "ix_attendance_face_settings_tenant_id" in index_names:
            op.drop_index("ix_attendance_face_settings_tenant_id", table_name="attendance_face_settings")

    if "attendance_employees" not in existing_tables:
        op.create_table(
        "attendance_employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_code", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("mobile", sa.String(length=50), nullable=True),
        sa.Column("gender", sa.String(length=20), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("designation", sa.String(length=100), nullable=True),
        sa.Column("shift_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_shifts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("joining_date", sa.Date(), nullable=True),
        sa.Column("employee_type", sa.String(length=50), nullable=False, server_default=sa.text("'Full Time'")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "employee_code", name="uq_attendance_employees_tenant_code"),
        sa.UniqueConstraint("tenant_id", "email", name="uq_attendance_employees_tenant_email"),
        )
        op.create_index("ix_attendance_employees_tenant_id", "attendance_employees", ["tenant_id"])
        op.create_index("ix_attendance_employees_shift_id", "attendance_employees", ["shift_id"])

    if "employee_face_profiles" not in existing_tables:
        op.create_table(
        "employee_face_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enrollment_status", sa.String(length=50), nullable=False, server_default=sa.text("'Not Enrolled'")),
        sa.Column("face_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("embedding_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("average_quality_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("last_enrolled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "employee_id", name="uq_employee_face_profiles_tenant_employee"),
        )
        op.create_index("ix_employee_face_profiles_tenant_id", "employee_face_profiles", ["tenant_id"])
        op.create_index("ix_employee_face_profiles_employee_id", "employee_face_profiles", ["employee_id"])

    if "employee_face_images" not in existing_tables:
        op.create_table(
        "employee_face_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("image_type", sa.String(length=50), nullable=True),
        sa.Column("quality_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("face_detected", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("face_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("validation_status", sa.String(length=50), nullable=False, server_default=sa.text("'Pending'")),
        sa.Column("validation_message", sa.Text(), nullable=True),
        sa.Column("embedding_generated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_employee_face_images_tenant_id", "employee_face_images", ["tenant_id"])
        op.create_index("ix_employee_face_images_employee_id", "employee_face_images", ["employee_id"])

    if "employee_face_embeddings" not in existing_tables:
        op.create_table(
        "employee_face_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("attendance_employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("face_image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employee_face_images.id", ondelete="SET NULL"), nullable=True),
        sa.Column("embedding", Vector(512), nullable=False),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("quality_score", sa.Numeric(10, 4), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index("ix_employee_face_embeddings_tenant_id", "employee_face_embeddings", ["tenant_id"])
        op.create_index("ix_employee_face_embeddings_employee_id", "employee_face_embeddings", ["employee_id"])
        op.create_index("ix_employee_face_embeddings_face_image_id", "employee_face_embeddings", ["face_image_id"])
        op.execute(
            "CREATE INDEX idx_employee_face_embeddings_vector ON employee_face_embeddings USING hnsw (embedding vector_cosine_ops)"
        )


def downgrade() -> None:
    op.drop_index("idx_employee_face_embeddings_vector", table_name="employee_face_embeddings")
    op.drop_index("ix_employee_face_embeddings_face_image_id", table_name="employee_face_embeddings")
    op.drop_index("ix_employee_face_embeddings_employee_id", table_name="employee_face_embeddings")
    op.drop_index("ix_employee_face_embeddings_tenant_id", table_name="employee_face_embeddings")
    op.drop_table("employee_face_embeddings")

    op.drop_index("ix_employee_face_images_employee_id", table_name="employee_face_images")
    op.drop_index("ix_employee_face_images_tenant_id", table_name="employee_face_images")
    op.drop_table("employee_face_images")

    op.drop_index("ix_employee_face_profiles_employee_id", table_name="employee_face_profiles")
    op.drop_index("ix_employee_face_profiles_tenant_id", table_name="employee_face_profiles")
    op.drop_table("employee_face_profiles")

    op.drop_index("ix_attendance_employees_shift_id", table_name="attendance_employees")
    op.drop_index("ix_attendance_employees_tenant_id", table_name="attendance_employees")
    op.drop_table("attendance_employees")

    op.drop_table("attendance_face_settings")

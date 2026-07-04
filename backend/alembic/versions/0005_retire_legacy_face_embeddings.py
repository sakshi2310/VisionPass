"""Retire legacy hash embeddings and use the production face model."""

from alembic import op


revision = "0005_retire_face_embeddings"
down_revision = "0004_add_employee_face_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TEMP TABLE affected_mock_face_profiles ON COMMIT DROP AS
        SELECT DISTINCT tenant_id, employee_id
        FROM employee_face_embeddings
        WHERE embedding_model = 'mock-face-embedder'
        """
    )
    op.execute(
        """
        UPDATE employee_face_embeddings
        SET is_active = FALSE
        WHERE embedding_model = 'mock-face-embedder'
        """
    )
    op.execute(
        """
        UPDATE employee_face_profiles AS profile
        SET embedding_count = active.count,
            enrollment_status = CASE WHEN active.count > 0 THEN 'Enrolled' ELSE 'Not Enrolled' END
        FROM (
            SELECT affected.tenant_id,
                   affected.employee_id,
                   (COUNT(embedding.id) FILTER (WHERE embedding.is_active))::integer AS count
            FROM affected_mock_face_profiles AS affected
            LEFT JOIN employee_face_embeddings AS embedding
              ON embedding.tenant_id = affected.tenant_id
             AND embedding.employee_id = affected.employee_id
            GROUP BY affected.tenant_id, affected.employee_id
        ) AS active
        WHERE profile.tenant_id = active.tenant_id
          AND profile.employee_id = active.employee_id
        """
    )
    op.execute(
        """
        UPDATE attendance_face_settings
        SET embedding_model = 'buffalo_l'
        WHERE embedding_model = 'mock-face-embedder'
        """
    )
    op.execute(
        """
        ALTER TABLE attendance_face_settings
        ALTER COLUMN embedding_model SET DEFAULT 'buffalo_l'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE attendance_face_settings
        ALTER COLUMN embedding_model SET DEFAULT 'mock-face-embedder'
        """
    )

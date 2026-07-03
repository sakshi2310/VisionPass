"""Schema bootstrap helpers."""

from sqlalchemy import text
from sqlalchemy.engine import Engine


def prepare_postgres_schema(engine: Engine) -> None:
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        connection.execute(
            text(
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
        )
        connection.execute(
            text(
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
        )
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE IF EXISTS tenants
                ADD COLUMN IF NOT EXISTS address VARCHAR(500)
                """
            )
        )

"""Create the complete, idempotent Vision Pass demo dataset."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.bootstrap_service import (  # noqa: E402
    DEMO_SUPER_ADMIN_EMAIL,
    DEMO_SUPER_ADMIN_PASSWORD,
    DEMO_TENANT_ADMIN_EMAIL,
    DEMO_TENANT_ADMIN_PASSWORD,
    DEMO_TENANT_USER_EMAIL,
    DEMO_TENANT_USER_PASSWORD,
    seed_default_admin,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply database migrations and seed all Vision Pass demo data.",
    )
    parser.add_argument(
        "--no-operational-data",
        action="store_true",
        help="Create accounts, tenant, and features without sample operational records.",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip Alembic migrations when the schema is already current.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow documented demo credentials when ENVIRONMENT=production.",
    )
    return parser.parse_args()


def run_migrations() -> None:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    config.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(config, "head")


def main() -> int:
    args = parse_args()
    if settings.environment.lower() == "production" and not args.force:
        print(
            "Refusing to install public demo credentials in production. "
            "Use --force only for an isolated demo environment.",
            file=sys.stderr,
        )
        return 2

    safe_database_url = make_url(settings.database_url).render_as_string(hide_password=True)
    print(f"Target database: {safe_database_url}")

    if not args.skip_migrations:
        print("Applying database migrations...")
        run_migrations()

    print("Seeding Vision Pass data...")
    db = SessionLocal()
    try:
        seed_default_admin(
            db,
            include_operational_data=not args.no_operational_data,
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("Seed completed successfully.")
    print("")
    print("Login credentials:")
    print(f"  Super Admin: {DEMO_SUPER_ADMIN_EMAIL} / {DEMO_SUPER_ADMIN_PASSWORD}")
    print(f"  Tenant Admin: {DEMO_TENANT_ADMIN_EMAIL} / {DEMO_TENANT_ADMIN_PASSWORD}")
    print(f"  Tenant User: {DEMO_TENANT_USER_EMAIL} / {DEMO_TENANT_USER_PASSWORD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

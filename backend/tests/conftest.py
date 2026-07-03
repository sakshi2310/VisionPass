"""Shared PostgreSQL integration-test setup."""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url


BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://visionpass:visionpass@localhost:5432/visionpass_test",
)

os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["JWT_SECRET"] = "vision-pass-integration-test-secret"
os.environ["ENVIRONMENT"] = "test"


def _create_test_database() -> None:
    url = make_url(TEST_DATABASE_URL)
    database_name = url.database or ""
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise RuntimeError("TEST_DATABASE_URL must use a simple PostgreSQL database name")

    admin_engine = create_engine(
        url.set(database="postgres"),
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
    )
    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
                {"database_name": database_name},
            ).scalar()
            if not exists:
                connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
    finally:
        admin_engine.dispose()


def _upgrade_test_database() -> None:
    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(alembic_config, "head")


_database_ready = False


def _truncate_application_tables() -> None:
    from app.db.session import engine

    table_names = [
        table_name
        for table_name in inspect(engine).get_table_names()
        if table_name != "alembic_version"
    ]
    if not table_names:
        return

    preparer = engine.dialect.identifier_preparer
    quoted_tables = ", ".join(preparer.quote(table_name) for table_name in table_names)
    with engine.begin() as connection:
        connection.exec_driver_sql(
            f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"
        )


@pytest.fixture()
def client():
    global _database_ready

    from fastapi.testclient import TestClient

    from app.main import app

    if not _database_ready:
        _create_test_database()
        _upgrade_test_database()
        _database_ready = True
    _truncate_application_tables()
    with TestClient(app) as test_client:
        yield test_client
    _truncate_application_tables()


@pytest.fixture()
def db(client):
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def tenant_admin_headers(client) -> dict[str, str]:
    response = client.post(
        "/api/tenant/auth/login",
        json={
            "email": "tenant.admin@visionpass.test",
            "password": "TenantAdmin@123",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def tenant_user_headers(client) -> dict[str, str]:
    response = client.post(
        "/api/user/auth/login",
        json={
            "email": "normal.user@visionpass.test",
            "password": "User@123456",
        },
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def super_admin_headers(client) -> dict[str, str]:
    response = client.post(
        "/api/admin/login",
        json={"email": "admin@gmail.com", "password": "admin@123"},
    )
    assert response.status_code == 200, response.text
    token = response.json()["token"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

"""Integration tests for attendance state transitions."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

BASE = "/api/attendance"
ADMIN_BASE = "/api/client-admin/attendance"


def _create_shift(client, headers, *, start_time="09:00:00"):
    response = client.post(
        f"{ADMIN_BASE}/shifts",
        headers=headers,
        json={
            "name": "Day Shift",
            "start_time": start_time,
            "end_time": "18:00:00",
            "grace_period_minutes": 0,
            "late_after_minutes": 0,
            "half_day_min_minutes": 240,
            "full_day_min_minutes": 480,
            "break_duration_minutes": 0,
            "is_default": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_employee(client, headers, code: str, shift_id: str | None = None):
    response = client.post(
        f"{ADMIN_BASE}/employees",
        headers=headers,
        json={
            "employee_code": code,
            "full_name": f"Employee {code}",
            "email": f"{code.lower()}@attendance.test",
            "shift_id": shift_id,
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _mark(client, headers, endpoint: str, employee_id: str, event_time: str):
    return client.post(
        f"{BASE}/{endpoint}",
        headers=headers,
        json={
            "employee_id": employee_id,
            "source": "manual",
            "event_time": event_time,
        },
    )


def test_first_check_in_creates_event_and_daily_record(client, tenant_admin_headers):
    shift = _create_shift(client, tenant_admin_headers)
    employee = _create_employee(client, tenant_admin_headers, "MARK-001", shift["id"])

    response = _mark(client, tenant_admin_headers, "check-in", employee["id"], "2026-07-01T03:30:00Z")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["event"]["event_type"] == "check_in"
    assert body["daily"]["first_check_in"] is not None
    assert body["daily"]["status"] == "present"


def test_duplicate_check_in_is_blocked(client, tenant_admin_headers):
    employee = _create_employee(client, tenant_admin_headers, "MARK-002")
    assert _mark(client, tenant_admin_headers, "check-in", employee["id"], "2026-07-01T03:30:00Z").status_code == 201

    duplicate = _mark(client, tenant_admin_headers, "check-in", employee["id"], "2026-07-01T03:35:00Z")

    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "DUPLICATE_CHECK_IN"


def test_check_out_after_check_in_updates_work_time(client, tenant_admin_headers):
    employee = _create_employee(client, tenant_admin_headers, "MARK-003")
    assert _mark(client, tenant_admin_headers, "check-in", employee["id"], "2026-07-01T03:30:00Z").status_code == 201

    response = _mark(client, tenant_admin_headers, "check-out", employee["id"], "2026-07-01T04:30:00Z")

    assert response.status_code == 201, response.text
    assert response.json()["event"]["event_type"] == "check_out"
    assert response.json()["daily"]["last_check_out"] is not None
    assert response.json()["daily"]["total_work_minutes"] == 60


def test_check_out_before_check_in_is_blocked(client, tenant_admin_headers):
    employee = _create_employee(client, tenant_admin_headers, "MARK-004")

    response = _mark(client, tenant_admin_headers, "check-out", employee["id"], "2026-07-01T04:30:00Z")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "CHECK_IN_REQUIRED"


def test_late_check_in_uses_environment_grace(client, tenant_admin_headers):
    shift = _create_shift(client, tenant_admin_headers)
    employee = _create_employee(client, tenant_admin_headers, "MARK-005", shift["id"])

    response = _mark(client, tenant_admin_headers, "check-in", employee["id"], "2026-07-01T03:41:00Z")

    assert response.status_code == 201, response.text
    assert response.json()["daily"]["status"] == "late"


def test_tenant_cannot_mark_another_tenants_employee(
    client,
    tenant_admin_headers,
    super_admin_headers,
):
    employee = _create_employee(client, tenant_admin_headers, "MARK-TENANT-A")
    created_tenant = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Attendance Tenant B",
            "email": "attendance-b@example.test",
            "password": "AttendanceB@123",
            "organization_name": "Attendance B",
            "slug": "attendance-b",
            "status": "active",
            "enabled_modules": ["attendance"],
        },
    )
    assert created_tenant.status_code == 201, created_tenant.text
    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "attendance-b@example.test", "password": "AttendanceB@123"},
    )
    assert login.status_code == 200, login.text
    tenant_b_headers = {
        "Authorization": f"Bearer {login.json()['token']['access_token']}"
    }

    response = _mark(client, tenant_b_headers, "check-in", employee["id"], "2026-07-01T03:30:00Z")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "EMPLOYEE_NOT_FOUND"

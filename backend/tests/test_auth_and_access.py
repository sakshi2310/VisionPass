"""Authentication, authorization, tenant isolation, and feature enforcement."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration

ATTENDANCE_BASE = "/api/client-admin/attendance"


def _create_shift(client, headers: dict[str, str], name: str = "General Shift"):
    response = client.post(
        f"{ATTENDANCE_BASE}/shifts",
        headers=headers,
        json={
            "name": name,
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "grace_period_minutes": 10,
            "late_after_minutes": 15,
            "half_day_min_minutes": 240,
            "full_day_min_minutes": 480,
            "break_duration_minutes": 30,
            "is_default": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_employee(client, headers: dict[str, str], code: str = "EMP-001"):
    response = client.post(
        f"{ATTENDANCE_BASE}/employees",
        headers=headers,
        json={
            "employee_code": code,
            "full_name": "Attendance Employee",
            "email": f"{code.lower()}@example.test",
            "department": "Operations",
            "designation": "Operator",
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_authentication_success_and_failure(client):
    tenant_admin = client.post(
        "/api/auth/login",
        json={
            "email": "tenant.admin@visionpass.test",
            "password": "TenantAdmin@123",
        },
    )
    assert tenant_admin.status_code == 200
    assert tenant_admin.json()["user"]["role"] == "tenant_admin"
    assert tenant_admin.json()["user"]["tenant_id"]
    assert tenant_admin.json()["access_token"]
    assert tenant_admin.json()["access_token"] == tenant_admin.json()["token"]["access_token"]
    assert tenant_admin.json()["token_type"] == "bearer"
    assert tenant_admin.json()["features"]

    tenant_user = client.post(
        "/api/auth/login",
        json={
            "email": "normal.user@visionpass.test",
            "password": "User@123456",
        },
    )
    assert tenant_user.status_code == 200
    assert tenant_user.json()["user"]["role"] == "user"
    assert tenant_user.json()["user"]["tenant_id"] == tenant_admin.json()["user"]["tenant_id"]
    assert tenant_user.json()["access_token"]

    super_admin = client.post(
        "/api/auth/login",
        json={"email": "admin@gmail.com", "password": "admin@123"},
    )
    assert super_admin.status_code == 200
    assert super_admin.json()["user"]["role"] == "super_admin"
    assert super_admin.json()["user"]["tenant_id"] is None
    assert super_admin.json()["tenant"] is None
    assert super_admin.json()["access_token"]

    failure = client.post(
        "/api/auth/login",
        json={
            "email": "tenant.admin@visionpass.test",
            "password": "incorrect-password",
        },
    )
    assert failure.status_code == 401


def test_jwt_protected_routes(client, tenant_admin_headers):
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.get("/api/auth/me", headers={"Authorization": "Bearer invalid-token"}).status_code
        == 401
    )

    response = client.get("/api/auth/me", headers=tenant_admin_headers)
    assert response.status_code == 200
    assert response.json()["email"] == "tenant.admin@visionpass.test"


def test_role_based_access_rejects_tenant_user(client, tenant_user_headers):
    response = client.get(f"{ATTENDANCE_BASE}/settings", headers=tenant_user_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant admin access required"


def test_attendance_feature_flag_is_enforced(
    client,
    tenant_admin_headers,
    super_admin_headers,
):
    initial = client.get(f"{ATTENDANCE_BASE}/settings", headers=tenant_admin_headers)
    assert initial.status_code == 200
    tenant_id = initial.json()["attendance_settings"]["tenant_id"]

    disabled = client.patch(
        f"/api/admin/tenants/{tenant_id}",
        headers=super_admin_headers,
        json={"enabled_modules": []},
    )
    assert disabled.status_code == 200, disabled.text

    blocked = client.get(f"{ATTENDANCE_BASE}/settings", headers=tenant_admin_headers)
    assert blocked.status_code == 403
    assert blocked.json()["detail"] == "Module access denied: attendance"


def test_tenant_resources_are_isolated(
    client,
    tenant_admin_headers,
    super_admin_headers,
):
    tenant_a_shift = _create_shift(client, tenant_admin_headers, "Tenant A Shift")
    tenant_a_employee = _create_employee(client, tenant_admin_headers, "TENANT-A-001")

    created_tenant = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Tenant B Admin",
            "email": "tenant-b-admin@example.test",
            "password": "TenantBAdmin@123",
            "organization_name": "Tenant B",
            "slug": "tenant-b",
            "status": "active",
            "enabled_modules": ["attendance"],
        },
    )
    assert created_tenant.status_code == 201, created_tenant.text

    tenant_b_login = client.post(
        "/api/tenant/auth/login",
        json={
            "email": "tenant-b-admin@example.test",
            "password": "TenantBAdmin@123",
        },
    )
    assert tenant_b_login.status_code == 200, tenant_b_login.text
    tenant_b_headers = {
        "Authorization": f"Bearer {tenant_b_login.json()['token']['access_token']}"
    }

    shifts = client.get(f"{ATTENDANCE_BASE}/shifts", headers=tenant_b_headers)
    employees = client.get(f"{ATTENDANCE_BASE}/employees", headers=tenant_b_headers)
    assert shifts.status_code == 200
    assert shifts.json()["shifts"] == []
    assert employees.status_code == 200
    assert employees.json()["employees"] == []

    assert (
        client.get(
            f"{ATTENDANCE_BASE}/shifts/{tenant_a_shift['id']}",
            headers=tenant_b_headers,
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"{ATTENDANCE_BASE}/employees/{tenant_a_employee['id']}",
            headers=tenant_b_headers,
        ).status_code
        == 404
    )

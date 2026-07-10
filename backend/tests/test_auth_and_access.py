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


def test_attendance_employee_creates_portal_user(client, tenant_admin_headers):
    created = client.post(
        f"{ATTENDANCE_BASE}/employees",
        headers=tenant_admin_headers,
        json={
            "employee_code": "EMP-LOGIN-1",
            "full_name": "Portal Linked Employee",
            "email": "portal.employee@example.test",
            "department": "Operations",
            "designation": "Operator",
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    payload = created.json()
    assert payload["employee"]["email"] == "portal.employee@example.test"
    assert payload["portal_account"]["created"] is True
    assert payload["portal_account"]["temporary_password"]
    assert payload["portal_account"]["role"] == "user"

    login = client.post(
        "/api/tenant/auth/login",
        json={
            "email": "portal.employee@example.test",
            "password": payload["portal_account"]["temporary_password"],
        },
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["role"] == "user"
    assert login.json()["user"]["employee_id"] == payload["employee"]["id"]

    attendance = client.get("/api/me/attendance", headers={"Authorization": f"Bearer {login.json()['token']['access_token']}"})
    assert attendance.status_code == 200, attendance.text
    assert attendance.json()["employee_linked"] is True


def test_tenant_admin_inherits_enabled_modules_from_tenant(client, super_admin_headers):
    created = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Attendance Admin",
            "email": "attendance.admin@example.test",
            "password": "AttendanceAdmin@123",
            "organization_name": "Attendance Tenant",
            "slug": "attendance-tenant",
            "status": "active",
            "enabled_modules": ["attendance"],
        },
    )
    assert created.status_code == 201, created.text

    login = client.post(
        "/api/tenant/auth/login",
        json={
            "email": "attendance.admin@example.test",
            "password": "AttendanceAdmin@123",
        },
    )
    assert login.status_code == 200, login.text
    assert "attendance" in login.json()["features"]
    assert login.json()["user"]["role"] == "tenant_admin"


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


def test_admin_tenant_list_handles_multiple_tenant_admins(client, tenant_admin_headers, super_admin_headers):
    created = client.post(
        "/api/tenant-admin/members",
        headers=tenant_admin_headers,
        json={
            "full_name": "Secondary Tenant Admin",
            "email": "secondary.admin@example.test",
            "password": "SecondaryAdmin@123",
            "role": "tenant_admin",
            "status": "active",
            "assigned_features": [],
        },
    )
    assert created.status_code == 201, created.text

    response = client.get("/api/admin/tenants", headers=super_admin_headers)
    assert response.status_code == 200, response.text
    tenants = response.json()
    assert tenants
    tenant = next(item for item in tenants if item["slug"] == "visionpass-platform")
    assert tenant["admin_email"] in {"tenant.admin@visionpass.test", "secondary.admin@example.test"}

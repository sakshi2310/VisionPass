"""Integration tests for tenant-admin portal-user role and feature assignment flows."""

from __future__ import annotations

import pytest

from app.models.member_feature import MemberFeature
from app.models.tenant_member import TenantMember

pytestmark = pytest.mark.integration


def _create_tenant_admin_workspace(client, super_admin_headers, *, slug: str = "feature-workspace"):
    response = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Workspace Admin",
            "email": "workspace-admin@example.test",
            "password": "WorkspaceAdmin@123",
            "organization_name": "Feature Workspace",
            "slug": slug,
            "status": "active",
            "enabled_modules": ["attendance", "visitor_unknown"],
        },
    )
    assert response.status_code == 201, response.text

    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "workspace-admin@example.test", "password": "WorkspaceAdmin@123"},
    )
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['token']['access_token']}"}
    return headers


def _create_portal_user(client, headers, *, email: str, password: str, role: str = "user", assigned_features: list[str] | None = None):
    response = client.post(
        "/api/tenant-admin/members",
        headers=headers,
        json={
            "full_name": "Portal User",
            "email": email,
            "password": password,
            "role": role,
            "status": "active",
            "assigned_features": assigned_features or [],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _member_feature_codes(db, member_id: str) -> list[str]:
    rows = (
        db.query(MemberFeature.feature_code)
        .filter(MemberFeature.tenant_member_id == member_id, MemberFeature.enabled.is_(True))
        .order_by(MemberFeature.feature_code.asc())
        .all()
    )
    return [feature_code for (feature_code,) in rows]


def test_role_changes_between_user_and_tenant_admin(client, db, super_admin_headers):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug="role-change-workspace")
    member = _create_portal_user(
        client,
        headers,
        email="role-change@example.test",
        password="PortalUser@123",
        role="user",
        assigned_features=[],
    )

    updated_to_admin = client.patch(
        f"/api/tenant-admin/members/{member['id']}",
        headers=headers,
        json={
            "role": "tenant_admin",
            "assigned_features": ["attendance"],
        },
    )
    assert updated_to_admin.status_code == 200, updated_to_admin.text
    assert updated_to_admin.json()["role"] == "TENANT_ADMIN"
    assert updated_to_admin.json()["assigned_features"] == ["attendance"]

    admin_login = client.post(
        "/api/tenant/auth/login",
        json={"email": "role-change@example.test", "password": "PortalUser@123"},
    )
    assert admin_login.status_code == 200, admin_login.text
    assert admin_login.json()["user"]["role"] == "tenant_admin"
    assert admin_login.json()["features"] == ["attendance"]

    updated_to_user = client.patch(
        f"/api/tenant-admin/members/{member['id']}",
        headers=headers,
        json={
            "role": "user",
            "assigned_features": [],
        },
    )
    assert updated_to_user.status_code == 200, updated_to_user.text
    assert updated_to_user.json()["role"] == "TENANT_USER"
    assert updated_to_user.json()["assigned_features"] == []

    user_login = client.post(
        "/api/user/auth/login",
        json={"email": "role-change@example.test", "password": "PortalUser@123"},
    )
    assert user_login.status_code == 200, user_login.text
    assert user_login.json()["user"]["role"] == "user"
    assert user_login.json()["features"] == []


@pytest.mark.parametrize(
    ("assigned_features",),
    [
        (["attendance"],),
        (["visitor_unknown"],),
        (["attendance", "visitor_unknown"],),
        ([],),
    ],
)
def test_feature_assignment_round_trip_matches_database(client, db, super_admin_headers, assigned_features):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug=f"round-trip-{len(assigned_features)}")
    member = _create_portal_user(
        client,
        headers,
        email=f"feature-round-trip-{len(assigned_features)}@example.test",
        password="PortalUser@123",
        role="tenant_admin",
        assigned_features=[],
    )

    updated = client.patch(
        f"/api/tenant-admin/members/{member['id']}",
        headers=headers,
        json={"assigned_features": assigned_features},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["assigned_features"] == assigned_features

    db_codes = _member_feature_codes(db, member["id"])
    assert db_codes == sorted(set(assigned_features))

    member_detail = client.get(f"/api/tenant-admin/members/{member['id']}", headers=headers)
    assert member_detail.status_code == 200, member_detail.text
    assert member_detail.json()["assigned_features"] == assigned_features


def test_removing_one_feature_replaces_previous_assignments(client, db, super_admin_headers):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug="replace-feature-workspace")
    member = _create_portal_user(
        client,
        headers,
        email="replace-feature@example.test",
        password="PortalUser@123",
        role="tenant_admin",
        assigned_features=["attendance", "visitor_unknown"],
    )

    updated = client.patch(
        f"/api/tenant-admin/members/{member['id']}",
        headers=headers,
        json={"assigned_features": ["attendance"]},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["assigned_features"] == ["attendance"]
    assert _member_feature_codes(db, member["id"]) == ["attendance"]


def test_clear_all_features(client, db, super_admin_headers):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug="clear-feature-workspace")
    member = _create_portal_user(
        client,
        headers,
        email="clear-features@example.test",
        password="PortalUser@123",
        role="tenant_admin",
        assigned_features=["attendance", "visitor_unknown"],
    )

    updated = client.patch(
        f"/api/tenant-admin/members/{member['id']}",
        headers=headers,
        json={"assigned_features": []},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["assigned_features"] == []
    assert _member_feature_codes(db, member["id"]) == []


def test_optional_apis_reject_users_without_required_feature(client, super_admin_headers):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug="access-check-workspace")
    member = _create_portal_user(
        client,
        headers,
        email="no-feature@example.test",
        password="PortalUser@123",
        role="tenant_admin",
        assigned_features=[],
    )

    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "no-feature@example.test", "password": "PortalUser@123"},
    )
    assert login.status_code == 200, login.text
    member_headers = {"Authorization": f"Bearer {login.json()['token']['access_token']}"}

    attendance = client.get("/api/client-admin/attendance/settings", headers=member_headers)
    assert attendance.status_code == 403
    assert attendance.json()["detail"] == "Module access denied: attendance"

    visitors = client.get("/api/visitors", headers=member_headers)
    assert visitors.status_code == 403
    assert visitors.json()["detail"] == "Module access denied: visitor_unknown"

    common_dashboard = client.get("/api/client-admin/dashboard", headers=member_headers)
    assert common_dashboard.status_code == 200, common_dashboard.text

    portal_users = client.get("/api/tenant-admin/members", headers=member_headers)
    assert portal_users.status_code == 200, portal_users.text


def test_assigning_features_unlocks_optional_apis(client, super_admin_headers):
    headers = _create_tenant_admin_workspace(client, super_admin_headers, slug="enabled-feature-workspace")
    member = _create_portal_user(
        client,
        headers,
        email="attendance-enabled@example.test",
        password="PortalUser@123",
        role="tenant_admin",
        assigned_features=["attendance", "visitor_unknown"],
    )

    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "attendance-enabled@example.test", "password": "PortalUser@123"},
    )
    assert login.status_code == 200, login.text
    member_headers = {"Authorization": f"Bearer {login.json()['token']['access_token']}"}

    attendance = client.get("/api/client-admin/attendance/settings", headers=member_headers)
    assert attendance.status_code == 200, attendance.text

    visitors = client.get("/api/visitors", headers=member_headers)
    assert visitors.status_code == 200, visitors.text


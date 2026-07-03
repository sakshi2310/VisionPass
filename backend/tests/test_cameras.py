"""Camera management integration tests."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

BASE = "/api/cameras"


def _payload(name: str = "Front Gate"):
    return {
        "name": name,
        "location": "Main entrance",
        "camera_type": "ip_webcam",
        "snapshot_url": "http://192.168.1.20:8080/shot.jpg",
        "stream_url": "http://192.168.1.20:8080/video",
        "username": "operator",
        "password": "camera-secret",
        "is_active": True,
    }


def test_create_update_and_delete_camera(client, tenant_admin_headers):
    created = client.post(BASE, headers=tenant_admin_headers, json=_payload())
    assert created.status_code == 201, created.text
    camera = created.json()
    assert camera["health_status"] == "unknown"
    assert camera["has_credentials"] is True
    assert "password" not in camera

    updated = client.put(
        f"{BASE}/{camera['id']}",
        headers=tenant_admin_headers,
        json={"name": "Front Gate Updated", "location": "Gate A"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Front Gate Updated"

    deleted = client.delete(f"{BASE}/{camera['id']}", headers=tenant_admin_headers)
    assert deleted.status_code == 204
    assert client.get(f"{BASE}/{camera['id']}", headers=tenant_admin_headers).status_code == 404


def test_tenant_user_permission_is_denied(client, tenant_user_headers):
    response = client.get(BASE, headers=tenant_user_headers)

    assert response.status_code == 403
    assert response.json()["detail"] == "Tenant admin access required"


def test_camera_is_tenant_isolated(client, tenant_admin_headers, super_admin_headers):
    created = client.post(BASE, headers=tenant_admin_headers, json=_payload("Tenant A Camera"))
    assert created.status_code == 201, created.text
    camera_id = created.json()["id"]

    tenant = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Camera Tenant Admin",
            "email": "camera-admin@example.test",
            "password": "CameraAdmin@123",
            "organization_name": "Camera Tenant",
            "slug": "camera-tenant",
            "status": "active",
            "enabled_modules": ["attendance"],
        },
    )
    assert tenant.status_code == 201, tenant.text
    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "camera-admin@example.test", "password": "CameraAdmin@123"},
    )
    assert login.status_code == 200, login.text
    other_headers = {"Authorization": f"Bearer {login.json()['token']['access_token']}"}

    assert client.get(f"{BASE}/{camera_id}", headers=other_headers).status_code == 404
    assert client.put(f"{BASE}/{camera_id}", headers=other_headers, json={"name": "Nope"}).status_code == 404
    assert client.delete(f"{BASE}/{camera_id}", headers=other_headers).status_code == 404

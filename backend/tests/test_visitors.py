"""Visitor management lifecycle, auditing, and isolation tests."""

from __future__ import annotations

import pytest

from app.models.audit_log import AuditLog

pytestmark = pytest.mark.integration

BASE = "/api/visitors"


def _payload(name: str = "Asha Visitor") -> dict:
    return {
        "full_name": name,
        "phone": "9876543210",
        "email": "asha@example.test",
        "company": "Example Co",
        "purpose": "Project meeting",
        "status": "expected",
    }


def test_create_check_in_check_out_and_history(client, db, tenant_admin_headers):
    created = client.post(BASE, headers=tenant_admin_headers, json=_payload())
    assert created.status_code == 201, created.text
    visitor = created.json()
    assert visitor["status"] == "expected"

    listed = client.get(BASE, headers=tenant_admin_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["visitors"]] == [visitor["id"]]

    updated = client.put(
        f"{BASE}/{visitor['id']}",
        headers=tenant_admin_headers,
        json={"purpose": "Updated meeting", "company": "Vision Partner"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["purpose"] == "Updated meeting"

    checked_in = client.post(
        f"{BASE}/{visitor['id']}/check-in",
        headers=tenant_admin_headers,
        json={"access_status": "granted", "notes": "Badge VP-10"},
    )
    assert checked_in.status_code == 200, checked_in.text
    assert checked_in.json()["visitor"]["status"] == "checked_in"
    visit_id = checked_in.json()["visit"]["id"]
    assert checked_in.json()["visit"]["check_out_time"] is None

    duplicate = client.post(
        f"{BASE}/{visitor['id']}/check-in",
        headers=tenant_admin_headers,
        json={},
    )
    assert duplicate.status_code == 409

    checked_out = client.post(
        f"{BASE}/{visitor['id']}/check-out",
        headers=tenant_admin_headers,
        json={"notes": "Badge returned"},
    )
    assert checked_out.status_code == 200, checked_out.text
    assert checked_out.json()["visitor"]["status"] == "checked_out"
    assert checked_out.json()["visit"]["id"] == visit_id
    assert checked_out.json()["visit"]["check_out_time"] is not None
    assert "Badge VP-10" in checked_out.json()["visit"]["notes"]
    assert "Badge returned" in checked_out.json()["visit"]["notes"]

    detail = client.get(f"{BASE}/{visitor['id']}", headers=tenant_admin_headers)
    assert detail.status_code == 200, detail.text
    assert len(detail.json()["visits"]) == 1
    assert detail.json()["visits"][0]["id"] == visit_id

    actions = {
        row.action
        for row in db.query(AuditLog)
        .filter(AuditLog.entity_id.in_([visitor["id"], visit_id]))
        .all()
    }
    assert {
        "visitor_created",
        "visitor_updated",
        "visitor_checked_in",
        "visitor_checked_out",
    }.issubset(actions)

    deleted = client.delete(f"{BASE}/{visitor['id']}", headers=tenant_admin_headers)
    assert deleted.status_code == 204
    assert client.get(f"{BASE}/{visitor['id']}", headers=tenant_admin_headers).status_code == 404
    assert db.query(AuditLog).filter(
        AuditLog.entity_id == visitor["id"],
        AuditLog.action == "visitor_deleted",
    ).one_or_none() is not None


def test_blocked_visitor_cannot_check_in(client, tenant_admin_headers):
    created = client.post(
        BASE,
        headers=tenant_admin_headers,
        json={**_payload("Blocked Visitor"), "status": "blocked"},
    )
    assert created.status_code == 201
    response = client.post(
        f"{BASE}/{created.json()['id']}/check-in",
        headers=tenant_admin_headers,
        json={},
    )
    assert response.status_code == 409


def test_visitors_are_tenant_isolated(client, tenant_admin_headers, super_admin_headers):
    created = client.post(BASE, headers=tenant_admin_headers, json=_payload("Tenant A Visitor"))
    assert created.status_code == 201
    visitor_id = created.json()["id"]

    tenant = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Visitor Tenant Admin",
            "email": "visitor-admin@example.test",
            "password": "VisitorAdmin@123",
            "organization_name": "Visitor Tenant",
            "slug": "visitor-tenant",
            "status": "active",
            "enabled_modules": [],
        },
    )
    assert tenant.status_code == 201, tenant.text
    login = client.post(
        "/api/tenant/auth/login",
        json={"email": "visitor-admin@example.test", "password": "VisitorAdmin@123"},
    )
    assert login.status_code == 200, login.text
    other_headers = {"Authorization": f"Bearer {login.json()['token']['access_token']}"}

    assert client.get(f"{BASE}/{visitor_id}", headers=other_headers).status_code == 404
    assert client.put(
        f"{BASE}/{visitor_id}",
        headers=other_headers,
        json={"purpose": "Leaked"},
    ).status_code == 404
    assert client.post(
        f"{BASE}/{visitor_id}/check-in",
        headers=other_headers,
        json={},
    ).status_code == 404
    assert client.post(
        f"{BASE}/{visitor_id}/check-out",
        headers=other_headers,
        json={},
    ).status_code == 404
    assert client.delete(f"{BASE}/{visitor_id}", headers=other_headers).status_code == 404
    assert client.get(BASE, headers=other_headers).json()["visitors"] == []


def test_visitor_permission_checks(client, tenant_user_headers, super_admin_headers):
    assert client.get(BASE).status_code == 401
    assert client.get(BASE, headers=tenant_user_headers).status_code == 403
    assert client.post(BASE, headers=tenant_user_headers, json=_payload()).status_code == 403
    assert client.get(BASE, headers=super_admin_headers).status_code == 403

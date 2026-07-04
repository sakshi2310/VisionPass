"""Alert creation, lifecycle, isolation, and permission tests."""

from __future__ import annotations

import pytest

from app.models.alert import Alert
from app.models.employee import AttendanceEmployee
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember

pytestmark = pytest.mark.integration

BASE = "/api/alerts"


def test_alert_created_acknowledged_and_resolved(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    employee = AttendanceEmployee(
        tenant_id=admin.tenant_id,
        employee_code="INACTIVE-ALERT",
        full_name="Inactive Alert Employee",
        email="inactive-alert@example.test",
        employee_type="Full Time",
        is_active=False,
    )
    db.add(employee)
    db.commit()

    decision = client.post(
        "/api/access/decision",
        headers=tenant_admin_headers,
        json={
            "tenant_id": admin.tenant_id,
            "employee_id": employee.id,
            "confidence": 0.95,
            "recognition_status": "MATCHED",
            "timestamp": "2026-07-02T10:00:00+05:30",
        },
    )
    assert decision.status_code == 200, decision.text
    assert decision.json()["decision"] == "denied"

    listed = client.get(BASE, headers=tenant_admin_headers)
    assert listed.status_code == 200, listed.text
    assert len(listed.json()["alerts"]) == 1
    alert = listed.json()["alerts"][0]
    assert alert["alert_type"] == "INACTIVE_EMPLOYEE_ATTEMPT"
    assert alert["severity"] == "critical"
    assert alert["status"] == "open"
    assert alert["metadata"]["employee_id"] == employee.id

    detail = client.get(f"{BASE}/{alert['id']}", headers=tenant_admin_headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == alert["id"]

    acknowledged = client.post(
        f"{BASE}/{alert['id']}/acknowledge",
        headers=tenant_admin_headers,
    )
    assert acknowledged.status_code == 200, acknowledged.text
    assert acknowledged.json()["status"] == "acknowledged"
    assert acknowledged.json()["acknowledged_at"] is not None

    acknowledged_filter = client.get(
        BASE,
        params={"status": "acknowledged"},
        headers=tenant_admin_headers,
    )
    assert [item["id"] for item in acknowledged_filter.json()["alerts"]] == [alert["id"]]

    resolved = client.post(
        f"{BASE}/{alert['id']}/resolve",
        headers=tenant_admin_headers,
    )
    assert resolved.status_code == 200, resolved.text
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["resolved_at"] is not None


def test_duplicate_attendance_attempt_creates_alert(client, tenant_admin_headers):
    employee = client.post(
        "/api/client-admin/attendance/employees",
        headers=tenant_admin_headers,
        json={
            "employee_code": "DUP-ALERT",
            "full_name": "Duplicate Alert Employee",
            "email": "duplicate-alert@example.test",
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert employee.status_code == 201, employee.text
    employee_id = employee.json()["id"]
    first = client.post(
        "/api/attendance/check-in",
        headers=tenant_admin_headers,
        json={
            "employee_id": employee_id,
            "source": "web",
            "event_time": "2026-07-02T03:30:00Z",
        },
    )
    assert first.status_code == 201, first.text
    duplicate = client.post(
        "/api/attendance/check-in",
        headers=tenant_admin_headers,
        json={
            "employee_id": employee_id,
            "source": "web",
            "event_time": "2026-07-02T03:31:00Z",
        },
    )
    assert duplicate.status_code == 409
    alerts = client.get(BASE, headers=tenant_admin_headers).json()["alerts"]
    assert len(alerts) == 1
    assert alerts[0]["alert_type"] == "DUPLICATE_ATTENDANCE_ATTEMPT"
    assert alerts[0]["source_id"] == employee_id


def test_alerts_are_tenant_isolated(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    own = Alert(
        tenant_id=admin.tenant_id,
        alert_type="CAMERA_OFFLINE",
        severity="high",
        title="Own camera offline",
        message="Own alert",
        status="open",
        source_type="camera",
        alert_metadata={},
    )
    foreign_tenant = Tenant(name="Foreign Alert Tenant", slug="foreign-alert", status="active")
    db.add_all([own, foreign_tenant])
    db.flush()
    foreign = Alert(
        tenant_id=foreign_tenant.id,
        alert_type="CAMERA_ERROR",
        severity="high",
        title="Foreign camera error",
        message="Foreign alert",
        status="open",
        source_type="camera",
        alert_metadata={},
    )
    db.add(foreign)
    db.commit()

    listed = client.get(BASE, headers=tenant_admin_headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["alerts"]] == [own.id]
    assert "Foreign camera error" not in listed.text
    assert client.get(f"{BASE}/{foreign.id}", headers=tenant_admin_headers).status_code == 404
    assert client.post(f"{BASE}/{foreign.id}/acknowledge", headers=tenant_admin_headers).status_code == 404
    assert client.post(f"{BASE}/{foreign.id}/resolve", headers=tenant_admin_headers).status_code == 404


def test_alert_permission_checks(client, tenant_user_headers, super_admin_headers):
    assert client.get(BASE).status_code == 401
    assert client.get(BASE, headers=tenant_user_headers).status_code == 403
    assert client.get(BASE, headers=super_admin_headers).status_code == 403

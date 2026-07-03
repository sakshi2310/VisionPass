"""Access decision rule and tenant-isolation integration tests."""

from __future__ import annotations

from datetime import date, time

import pytest

from app.models.access_event import AccessLog
from app.models.attendance import AttendanceHoliday, AttendanceShift
from app.models.employee import AttendanceEmployee
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.visitor import Visitor

pytestmark = pytest.mark.integration

DECISION = "/api/access/decision"
LOGS = "/api/access/logs"


def _employee(tenant_id: str, code: str, *, active: bool = True) -> AttendanceEmployee:
    return AttendanceEmployee(
        tenant_id=tenant_id,
        employee_code=code,
        full_name=f"Employee {code}",
        email=f"{code.lower()}@example.test",
        employee_type="Full Time",
        is_active=active,
    )


def _request(
    tenant_id: str,
    *,
    employee_id: str | None = None,
    visitor_id: str | None = None,
    confidence: float | None = 0.95,
    recognition_status: str = "MATCHED",
    timestamp: str = "2026-07-02T10:00:00+05:30",
) -> dict:
    return {
        "tenant_id": tenant_id,
        "employee_id": employee_id,
        "visitor_id": visitor_id,
        "confidence": confidence,
        "recognition_status": recognition_status,
        "timestamp": timestamp,
    }


def test_granted_employee_during_shift(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    shift = AttendanceShift(
        tenant_id=admin.tenant_id,
        name="Day Shift",
        start_time=time(9),
        end_time=time(18),
        grace_period_minutes=0,
        late_after_minutes=0,
        half_day_min_minutes=240,
        full_day_min_minutes=480,
        break_duration_minutes=0,
        is_default=True,
        is_active=True,
    )
    employee = _employee(admin.tenant_id, "ACTIVE")
    db.add_all([shift, employee])
    db.flush()
    employee.shift_id = shift.id
    db.commit()

    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(admin.tenant_id, employee_id=employee.id),
    )
    assert response.status_code == 200, response.text
    assert response.json()["decision"] == "granted"
    assert response.json()["reason"] == "active_employee_within_allowed_time"
    assert response.json()["log"]["employee_id"] == employee.id

    logs = client.get(LOGS, headers=tenant_admin_headers)
    assert logs.status_code == 200
    assert len(logs.json()["logs"]) == 1
    assert logs.json()["logs"][0]["identity_name"] == employee.full_name


def test_inactive_employee_is_denied(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    employee = _employee(admin.tenant_id, "INACTIVE", active=False)
    db.add(employee)
    db.commit()

    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(admin.tenant_id, employee_id=employee.id),
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "denied"
    assert response.json()["reason"] == "inactive_employee"


def test_unknown_face_uses_configured_manual_review(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(
            admin.tenant_id,
            confidence=None,
            recognition_status="UNKNOWN",
        ),
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "manual_review"
    assert response.json()["reason"] == "unknown_face"
    assert response.json()["log"]["employee_id"] is None


def test_low_confidence_requires_manual_review(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    employee = _employee(admin.tenant_id, "LOW")
    db.add(employee)
    db.commit()
    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(
            admin.tenant_id,
            employee_id=employee.id,
            confidence=0.30,
            recognition_status="LOW_CONFIDENCE",
        ),
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "manual_review"
    assert response.json()["reason"] == "low_confidence"


def test_blocked_visitor_is_denied(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    visitor = Visitor(
        tenant_id=admin.tenant_id,
        full_name="Blocked Guest",
        phone="9999999999",
        purpose="Visit",
        status="blocked",
    )
    db.add(visitor)
    db.commit()
    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(admin.tenant_id, visitor_id=visitor.id),
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "denied"
    assert response.json()["reason"] == "blocked_visitor"


def test_holiday_and_outside_shift_use_configured_policy(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    shift = AttendanceShift(
        tenant_id=admin.tenant_id,
        name="Day Shift",
        start_time=time(9),
        end_time=time(18),
        grace_period_minutes=0,
        late_after_minutes=0,
        half_day_min_minutes=240,
        full_day_min_minutes=480,
        break_duration_minutes=0,
        is_default=True,
        is_active=True,
    )
    employee = _employee(admin.tenant_id, "POLICY")
    db.add_all([shift, employee])
    db.flush()
    employee.shift_id = shift.id
    db.commit()

    outside = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(
            admin.tenant_id,
            employee_id=employee.id,
            timestamp="2026-07-02T21:00:00+05:30",
        ),
    )
    assert outside.status_code == 200
    assert outside.json()["decision"] == "manual_review"
    assert outside.json()["reason"] == "outside_shift"

    db.add(AttendanceHoliday(
        tenant_id=admin.tenant_id,
        holiday_name="Test Holiday",
        holiday_date=date(2026, 7, 3),
        is_active=True,
    ))
    db.commit()
    holiday = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(
            admin.tenant_id,
            employee_id=employee.id,
            timestamp="2026-07-03T10:00:00+05:30",
        ),
    )
    assert holiday.status_code == 200
    assert holiday.json()["decision"] == "manual_review"
    assert holiday.json()["reason"] == "holiday"


def test_access_logs_are_tenant_isolated(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    foreign_tenant = Tenant(name="Foreign Access Tenant", slug="foreign-access", status="active")
    db.add(foreign_tenant)
    db.flush()
    foreign_employee = _employee(foreign_tenant.id, "FOREIGN")
    db.add(foreign_employee)
    db.flush()
    db.add(AccessLog(
        tenant_id=foreign_tenant.id,
        employee_id=foreign_employee.id,
        decision="granted",
        reason="foreign",
        confidence=0.99,
    ))
    db.commit()

    response = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(admin.tenant_id, employee_id=foreign_employee.id),
    )
    assert response.status_code == 200
    assert response.json()["decision"] == "denied"
    assert response.json()["reason"] == "employee_not_found"
    assert response.json()["log"]["employee_id"] is None

    logs = client.get(LOGS, headers=tenant_admin_headers)
    assert logs.status_code == 200
    assert len(logs.json()["logs"]) == 1
    assert logs.json()["logs"][0]["tenant_id"] == admin.tenant_id
    assert "foreign" not in logs.text

    mismatch = client.post(
        DECISION,
        headers=tenant_admin_headers,
        json=_request(foreign_tenant.id, employee_id=foreign_employee.id),
    )
    assert mismatch.status_code == 403


def test_access_permissions(client, tenant_user_headers, super_admin_headers):
    assert client.get(LOGS).status_code == 401
    assert client.get(LOGS, headers=tenant_user_headers).status_code == 403
    assert client.get(LOGS, headers=super_admin_headers).status_code == 403

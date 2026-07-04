"""Operational report API integration tests."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.models.access_event import AccessLog
from app.models.attendance import DailyAttendanceRecord
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.models.visitor import Visitor, VisitorVisit

pytestmark = pytest.mark.integration


def _employee(tenant_id: str, code: str, department: str = "Engineering") -> AttendanceEmployee:
    return AttendanceEmployee(
        tenant_id=tenant_id,
        employee_code=code,
        full_name=f"Employee {code}",
        email=f"{code.lower()}@reports.test",
        department=department,
        employee_type="Full Time",
        is_active=True,
    )


def _seed_report_data(db, tenant_id: str, code: str = "RPT"):
    employee = _employee(tenant_id, code)
    camera = Camera(
        tenant_id=tenant_id,
        name=f"Camera {code}",
        location="Main gate",
        camera_type="manual",
        is_active=True,
        health_status="online",
    )
    visitor = Visitor(
        tenant_id=tenant_id,
        full_name=f"Visitor {code}",
        phone="9000000000",
        purpose="Meeting",
        host_employee_id=None,
        status="checked_in",
    )
    db.add_all([employee, camera, visitor])
    db.flush()
    visitor.host_employee_id = employee.id
    timestamp = datetime(2026, 7, 2, 8, 30, tzinfo=timezone.utc)
    attendance = DailyAttendanceRecord(
        tenant_id=tenant_id,
        employee_id=employee.id,
        attendance_date=date(2026, 7, 2),
        first_check_in=timestamp,
        total_work_minutes=480,
        status="present",
    )
    camera_event = CameraEvent(
        tenant_id=tenant_id,
        camera_id=camera.id,
        event_type="recognition",
        employee_id=employee.id,
        recognition_status="MATCHED",
        confidence=0.96,
        created_at=timestamp,
    )
    visit = VisitorVisit(
        tenant_id=tenant_id,
        visitor_id=visitor.id,
        check_in_time=timestamp,
        access_status="granted",
    )
    access = AccessLog(
        tenant_id=tenant_id,
        employee_id=employee.id,
        camera_id=camera.id,
        decision="granted",
        reason="active_employee_within_allowed_time",
        confidence=0.96,
        created_at=timestamp,
    )
    db.add_all([attendance, camera_event, visit, access])
    db.commit()
    return employee, camera


def test_all_report_endpoints_return_real_tenant_data(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    employee, camera = _seed_report_data(db, admin.tenant_id)

    expectations = {
        "attendance": "employee_name",
        "employees": "full_name",
        "visitors": "host_employee_name",
        "cameras": "event_count",
        "recognition": "recognition_status",
        "access": "decision",
    }
    for report, expected_key in expectations.items():
        response = client.get(f"/api/reports/{report}", headers=tenant_admin_headers)
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["total"] == 1
        assert expected_key in payload["items"][0]

    filtered = client.get(
        "/api/reports/recognition",
        headers=tenant_admin_headers,
        params={
            "start_date": "2026-07-02",
            "end_date": "2026-07-02",
            "employee_id": employee.id,
            "department": "engineering",
            "status": "matched",
            "camera_id": camera.id,
            "event_type": "recognition",
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 1

    no_match = client.get(
        "/api/reports/access",
        headers=tenant_admin_headers,
        params={"status": "denied"},
    )
    assert no_match.status_code == 200
    assert no_match.json() == {"items": [], "total": 0}


def test_reports_are_tenant_isolated(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    _seed_report_data(db, admin.tenant_id, "LOCAL")
    foreign = Tenant(name="Foreign Reports", slug="foreign-reports", status="active")
    db.add(foreign)
    db.flush()
    _seed_report_data(db, foreign.id, "SECRET")

    for report in ("attendance", "employees", "visitors", "cameras", "recognition", "access"):
        response = client.get(f"/api/reports/{report}", headers=tenant_admin_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert "SECRET" not in response.text


def test_report_csv_exports_and_date_validation(client, db, tenant_admin_headers):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    _seed_report_data(db, admin.tenant_id)

    attendance = client.get("/api/reports/attendance/export.csv", headers=tenant_admin_headers)
    assert attendance.status_code == 200
    assert attendance.headers["content-type"].startswith("text/csv")
    assert "attachment; filename=\"attendance-report.csv\"" == attendance.headers["content-disposition"]
    assert "employee_name" in attendance.text
    assert "Employee RPT" in attendance.text

    access = client.get("/api/reports/access/export.csv", headers=tenant_admin_headers)
    assert access.status_code == 200
    assert "active_employee_within_allowed_time" in access.text

    invalid = client.get(
        "/api/reports/attendance",
        headers=tenant_admin_headers,
        params={"start_date": "2026-07-03", "end_date": "2026-07-02"},
    )
    assert invalid.status_code == 422


def test_report_permissions(client, tenant_user_headers, super_admin_headers):
    for path in ("/api/reports/attendance", "/api/reports/access/export.csv"):
        assert client.get(path).status_code == 401
        assert client.get(path, headers=tenant_user_headers).status_code == 403
        assert client.get(path, headers=super_admin_headers).status_code == 403

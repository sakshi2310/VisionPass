"""Tenant-user personal workspace and isolation tests."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models.attendance import AttendanceShift, DailyAttendanceRecord
from app.models.employee import AttendanceEmployee, EmployeeFaceProfile
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember

pytestmark = pytest.mark.integration

BASE = "/api/me"


def _employee(tenant_id: str, code: str) -> AttendanceEmployee:
    return AttendanceEmployee(
        tenant_id=tenant_id,
        employee_code=code,
        full_name=f"Employee {code}",
        email=f"{code.lower()}@example.test",
        department="Engineering",
        designation="Engineer",
        employee_type="Full Time",
        is_active=True,
    )


def test_me_endpoints_return_only_authenticated_users_employee_data(
    client,
    db,
    tenant_user_headers,
):
    member = db.query(TenantMember).filter(TenantMember.email == "normal.user@visionpass.test").one()
    shift = AttendanceShift(
        tenant_id=member.tenant_id,
        name="General",
        start_time=time(9),
        end_time=time(18),
        grace_period_minutes=10,
        late_after_minutes=10,
        half_day_min_minutes=240,
        full_day_min_minutes=480,
        break_duration_minutes=0,
        is_default=True,
        is_active=True,
    )
    own_employee = _employee(member.tenant_id, "OWN")
    other_employee = _employee(member.tenant_id, "OTHER")
    db.add_all([shift, own_employee, other_employee])
    db.flush()
    own_employee.shift_id = shift.id
    other_employee.shift_id = shift.id
    member.employee_id = own_employee.id

    zone = ZoneInfo("Asia/Kolkata")
    today = datetime.now(zone).date()
    check_in = datetime.combine(today, time(9, 20), zone).astimezone(timezone.utc)
    check_out = check_in + timedelta(hours=8)
    own_record = DailyAttendanceRecord(
        tenant_id=member.tenant_id,
        employee_id=own_employee.id,
        attendance_date=today,
        first_check_in=check_in,
        last_check_out=check_out,
        total_work_minutes=480,
        status="late",
        shift_id=shift.id,
    )
    other_record = DailyAttendanceRecord(
        tenant_id=member.tenant_id,
        employee_id=other_employee.id,
        attendance_date=today,
        first_check_in=check_in,
        total_work_minutes=0,
        status="present",
        shift_id=shift.id,
    )
    face_profile = EmployeeFaceProfile(
        tenant_id=member.tenant_id,
        employee_id=own_employee.id,
        enrollment_status="Enrolled",
        face_count=4,
        embedding_count=4,
    )
    db.add_all([own_record, other_record, face_profile, member])
    db.commit()

    dashboard = client.get(f"{BASE}/dashboard", headers=tenant_user_headers)
    assert dashboard.status_code == 200, dashboard.text
    assert dashboard.json()["today_status"] == "late"
    assert dashboard.json()["working_hours"] == 8
    assert dashboard.json()["current_shift"]["name"] == "General"
    assert dashboard.json()["monthly_summary"]["late"] == 1
    assert dashboard.json()["monthly_summary"]["present"] == 0

    attendance = client.get(
        f"{BASE}/attendance",
        params={"month": today.strftime("%Y-%m")},
        headers=tenant_user_headers,
    )
    assert attendance.status_code == 200, attendance.text
    assert len(attendance.json()["days"]) == 1
    assert attendance.json()["days"][0]["status"] == "late"

    profile = client.get(f"{BASE}/profile", headers=tenant_user_headers)
    assert profile.status_code == 200, profile.text
    assert profile.json()["employee_id"] == own_employee.id
    assert profile.json()["employee_code"] == "OWN"
    assert profile.json()["face_enrollment_status"] == "Enrolled"
    assert profile.json()["face_count"] == 4

    notifications = client.get(f"{BASE}/notifications", headers=tenant_user_headers)
    assert notifications.status_code == 200, notifications.text
    assert len(notifications.json()["notifications"]) == 1
    assert own_record.id in notifications.json()["notifications"][0]["id"]
    assert other_record.id not in notifications.text

    legacy_today = client.get("/api/attendance/today", headers=tenant_user_headers)
    assert legacy_today.status_code == 200, legacy_today.text
    assert len(legacy_today.json()["records"]) == 1
    assert legacy_today.json()["records"][0]["employee_code"] == "OWN"

    forbidden_mark = client.post(
        "/api/attendance/check-in",
        headers=tenant_user_headers,
        json={"employee_id": other_employee.id, "source": "web"},
    )
    assert forbidden_mark.status_code == 403


def test_me_rejects_admins_and_management_endpoints_reject_users(
    client,
    tenant_admin_headers,
    tenant_user_headers,
):
    for path in ("dashboard", "attendance", "profile", "notifications"):
        assert client.get(f"{BASE}/{path}", headers=tenant_admin_headers).status_code == 403

    assert client.get("/api/client-admin/attendance/employees", headers=tenant_user_headers).status_code == 403
    assert client.get("/api/client-admin/attendance/settings", headers=tenant_user_headers).status_code == 403
    assert client.get("/api/cameras", headers=tenant_user_headers).status_code == 403
    assert client.get("/api/client-admin/dashboard/summary", headers=tenant_user_headers).status_code == 403
    assert client.post("/api/attendance/recognize", headers=tenant_user_headers).status_code == 403
    assert client.post("/api/attendance/recognize-and-mark", headers=tenant_user_headers).status_code == 403


def test_foreign_tenant_employee_link_is_never_followed(client, db, tenant_user_headers):
    member = db.query(TenantMember).filter(TenantMember.email == "normal.user@visionpass.test").one()
    foreign_tenant = Tenant(name="Foreign Tenant", slug="me-foreign", status="active")
    db.add(foreign_tenant)
    db.flush()
    foreign_employee = _employee(foreign_tenant.id, "FOREIGN")
    db.add(foreign_employee)
    db.flush()
    member.employee_id = foreign_employee.id
    db.add(member)
    db.commit()

    dashboard = client.get(f"{BASE}/dashboard", headers=tenant_user_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["employee_linked"] is False
    assert dashboard.json()["today_status"] == "not_marked"

    attendance = client.get(f"{BASE}/attendance", headers=tenant_user_headers)
    assert attendance.status_code == 200
    assert attendance.json()["employee_linked"] is False
    assert attendance.json()["days"] == []

    profile = client.get(f"{BASE}/profile", headers=tenant_user_headers)
    assert profile.status_code == 200
    assert profile.json()["employee_id"] is None
    assert profile.json()["employee_code"] is None


def test_me_requires_authentication_and_validates_month(client, tenant_user_headers):
    assert client.get(f"{BASE}/dashboard").status_code == 401
    assert client.get(f"{BASE}/attendance", params={"month": "2026-13"}, headers=tenant_user_headers).status_code == 422

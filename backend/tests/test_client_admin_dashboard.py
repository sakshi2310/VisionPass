"""Client-admin dashboard integration tests."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest

from app.models.attendance import AttendanceEvent, DailyAttendanceRecord
from app.models.alert import Alert
from app.models.camera import Camera, CameraEvent
from app.models.employee import AttendanceEmployee
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember

pytestmark = pytest.mark.integration

BASE = "/api/client-admin/dashboard"


def _employee(tenant_id: str, code: str, *, active: bool = True) -> AttendanceEmployee:
    return AttendanceEmployee(
        tenant_id=tenant_id,
        employee_code=code,
        full_name=f"Employee {code}",
        email=f"{code.lower()}@example.test",
        employee_type="Full Time",
        is_active=active,
    )


def test_dashboard_returns_real_tenant_scoped_summary_and_activity(
    client,
    db,
    tenant_admin_headers,
):
    admin = db.query(TenantMember).filter(TenantMember.email == "tenant.admin@visionpass.test").one()
    other_tenant = Tenant(name="Other Tenant", slug="dashboard-other", status="active")
    db.add(other_tenant)
    db.flush()

    present = _employee(admin.tenant_id, "PRESENT")
    late = _employee(admin.tenant_id, "LATE")
    absent = _employee(admin.tenant_id, "ABSENT")
    inactive = _employee(admin.tenant_id, "INACTIVE", active=False)
    foreign_employee = _employee(other_tenant.id, "FOREIGN")
    db.add_all([present, late, absent, inactive, foreign_employee])
    db.flush()

    online_camera = Camera(
        tenant_id=admin.tenant_id,
        name="Front Gate",
        location="Entrance",
        camera_type="manual",
        is_active=True,
        health_status="online",
    )
    offline_camera = Camera(
        tenant_id=admin.tenant_id,
        name="Rear Gate",
        location="Rear",
        camera_type="manual",
        is_active=True,
        health_status="offline",
    )
    inactive_camera = Camera(
        tenant_id=admin.tenant_id,
        name="Disabled",
        location="Storage",
        camera_type="manual",
        is_active=False,
        health_status="error",
    )
    foreign_camera = Camera(
        tenant_id=other_tenant.id,
        name="Foreign Camera",
        location="Elsewhere",
        camera_type="manual",
        is_active=True,
        health_status="offline",
    )
    db.add_all([online_camera, offline_camera, inactive_camera, foreign_camera])
    db.flush()

    now = datetime.now(timezone.utc)
    db.add_all(
        [
            DailyAttendanceRecord(
                tenant_id=admin.tenant_id,
                employee_id=present.id,
                attendance_date=now.astimezone(ZoneInfo("Asia/Kolkata")).date(),
                status="present",
            ),
            DailyAttendanceRecord(
                tenant_id=admin.tenant_id,
                employee_id=late.id,
                attendance_date=now.astimezone(ZoneInfo("Asia/Kolkata")).date(),
                status="late",
            ),
            DailyAttendanceRecord(
                tenant_id=other_tenant.id,
                employee_id=foreign_employee.id,
                attendance_date=now.astimezone(ZoneInfo("Asia/Kolkata")).date(),
                status="late",
            ),
            AttendanceEvent(
                tenant_id=admin.tenant_id,
                employee_id=present.id,
                event_type="check_in",
                source="camera",
                camera_id=online_camera.id,
                confidence=0.94,
                event_time=now,
            ),
            AttendanceEvent(
                tenant_id=other_tenant.id,
                employee_id=foreign_employee.id,
                event_type="check_in",
                source="camera",
                camera_id=foreign_camera.id,
                confidence=0.99,
                event_time=now,
            ),
            CameraEvent(
                tenant_id=admin.tenant_id,
                camera_id=online_camera.id,
                event_type="recognition",
                recognition_status="UNKNOWN",
                confidence=0.2,
                created_at=now,
            ),
            Alert(
                tenant_id=admin.tenant_id,
                alert_type="UNKNOWN_FACE",
                severity="high",
                title="Unknown face detected",
                message="Unknown face",
                status="open",
                source_type="face_recognition",
                alert_metadata={},
                created_at=now,
            ),
            CameraEvent(
                tenant_id=admin.tenant_id,
                camera_id=online_camera.id,
                employee_id=present.id,
                event_type="recognition",
                recognition_status="MATCHED",
                confidence=0.94,
                created_at=now,
            ),
            CameraEvent(
                tenant_id=other_tenant.id,
                camera_id=foreign_camera.id,
                event_type="recognition",
                recognition_status="UNKNOWN",
                confidence=0.1,
                created_at=now,
            ),
            Alert(
                tenant_id=other_tenant.id,
                alert_type="UNKNOWN_FACE",
                severity="high",
                title="Unknown face detected",
                message="Foreign unknown face",
                status="open",
                source_type="face_recognition",
                alert_metadata={},
                created_at=now,
            ),
        ]
    )
    db.commit()

    summary_response = client.get(f"{BASE}/summary", headers=tenant_admin_headers)
    assert summary_response.status_code == 200, summary_response.text
    assert summary_response.json() == {
        "total_employees": 4,
        "active_employees": 3,
        "today_present": 2,
        "today_absent": 1,
        "today_late": 1,
        "active_cameras": 2,
        "offline_cameras": 1,
        "unknown_face_alerts": 1,
    }

    activity_response = client.get(f"{BASE}/recent-activity", headers=tenant_admin_headers)
    assert activity_response.status_code == 200, activity_response.text
    activity = activity_response.json()
    assert len(activity["attendance_events"]) == 1
    assert activity["attendance_events"][0]["employee_code"] == "PRESENT"
    assert activity["attendance_events"][0]["camera_name"] == "Front Gate"
    assert len(activity["recognition_attempts"]) == 2
    assert {item["recognition_status"] for item in activity["recognition_attempts"]} == {"MATCHED", "UNKNOWN"}
    assert all(item["camera_name"] != "Foreign Camera" for item in activity["recognition_attempts"])


def test_dashboard_rejects_tenant_users(client, tenant_user_headers):
    assert client.get(f"{BASE}/summary", headers=tenant_user_headers).status_code == 403
    assert client.get(f"{BASE}/recent-activity", headers=tenant_user_headers).status_code == 403


def test_dashboard_requires_authentication(client):
    assert client.get(f"{BASE}/summary").status_code == 401
    assert client.get(f"{BASE}/recent-activity").status_code == 401

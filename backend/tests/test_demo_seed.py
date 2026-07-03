"""MVP demo seed completeness and idempotency."""

from __future__ import annotations

import pytest

from app.models.alert import Alert
from app.models.attendance import AttendanceEvent, AttendanceHoliday, AttendanceShift, DailyAttendanceRecord
from app.models.camera import Camera
from app.models.employee import AttendanceEmployee, EmployeeFaceEmbedding
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.services.bootstrap_service import seed_default_admin

pytestmark = pytest.mark.integration


def test_demo_seed_is_complete_idempotent_and_has_no_fake_embeddings(db):
    seed_default_admin(db)

    tenant = db.query(Tenant).filter(Tenant.slug == "visionpass-demo").one()
    first_counts = {
        "admins": db.query(SuperAdmin).count(),
        "members": db.query(TenantMember).filter(TenantMember.tenant_id == tenant.id).count(),
        "employees": db.query(AttendanceEmployee).filter(AttendanceEmployee.tenant_id == tenant.id).count(),
        "shifts": db.query(AttendanceShift).filter(AttendanceShift.tenant_id == tenant.id).count(),
        "holidays": db.query(AttendanceHoliday).filter(AttendanceHoliday.tenant_id == tenant.id).count(),
        "cameras": db.query(Camera).filter(Camera.tenant_id == tenant.id).count(),
        "daily": db.query(DailyAttendanceRecord).filter(DailyAttendanceRecord.tenant_id == tenant.id).count(),
        "events": db.query(AttendanceEvent).filter(AttendanceEvent.tenant_id == tenant.id).count(),
        "alerts": db.query(Alert).filter(Alert.tenant_id == tenant.id).count(),
    }

    assert first_counts["admins"] >= 1
    assert first_counts["members"] >= 2
    assert first_counts["employees"] == 3
    assert first_counts["shifts"] == 1
    assert first_counts["holidays"] == 1
    assert first_counts["cameras"] == 2
    assert first_counts["daily"] == 6
    assert first_counts["events"] == 8
    assert first_counts["alerts"] == 1
    assert db.query(EmployeeFaceEmbedding).filter(EmployeeFaceEmbedding.tenant_id == tenant.id).count() == 0

    seed_default_admin(db)
    second_counts = {
        "admins": db.query(SuperAdmin).count(),
        "members": db.query(TenantMember).filter(TenantMember.tenant_id == tenant.id).count(),
        "employees": db.query(AttendanceEmployee).filter(AttendanceEmployee.tenant_id == tenant.id).count(),
        "shifts": db.query(AttendanceShift).filter(AttendanceShift.tenant_id == tenant.id).count(),
        "holidays": db.query(AttendanceHoliday).filter(AttendanceHoliday.tenant_id == tenant.id).count(),
        "cameras": db.query(Camera).filter(Camera.tenant_id == tenant.id).count(),
        "daily": db.query(DailyAttendanceRecord).filter(DailyAttendanceRecord.tenant_id == tenant.id).count(),
        "events": db.query(AttendanceEvent).filter(AttendanceEvent.tenant_id == tenant.id).count(),
        "alerts": db.query(Alert).filter(Alert.tenant_id == tenant.id).count(),
    }
    assert second_counts == first_counts

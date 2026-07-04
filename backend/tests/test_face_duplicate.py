"""Unit tests for tenant-scoped duplicate vector lookup."""

from app.core.config import settings
from app.services.employee_service import find_duplicate_face


class _FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _FakeSession:
    def __init__(self, row):
        self.row = row
        self.statement = None
        self.parameters = None

    def execute(self, statement, parameters):
        self.statement = statement
        self.parameters = parameters
        return _FakeResult(self.row)


def test_duplicate_lookup_is_tenant_scoped_and_uses_configured_threshold():
    db = _FakeSession(
        {
            "employee_id": "other-employee",
            "employee_name": "Other Employee",
            "distance": 0.05,
            "similarity": 0.95,
        }
    )

    duplicate = find_duplicate_face(
        db,
        tenant_id="tenant-a",
        employee_id="new-employee",
        embedding=[1.0, *([0.0] * 511)],
    )

    assert db.parameters["tenant_id"] == "tenant-a"
    assert db.parameters["employee_id"] == "new-employee"
    assert db.parameters["duplicate_threshold"] == settings.face_duplicate_threshold
    assert "face.tenant_id = :tenant_id" in str(db.statement)
    assert duplicate == {
        "employee_id": "other-employee",
        "employee_name": "Other Employee",
        "distance": 0.05,
        "similarity": 0.95,
    }


def test_duplicate_lookup_returns_none_when_tenant_has_no_match():
    db = _FakeSession(None)

    duplicate = find_duplicate_face(
        db,
        tenant_id="tenant-b",
        employee_id="employee-b",
        embedding=[1.0, *([0.0] * 511)],
    )

    assert duplicate is None

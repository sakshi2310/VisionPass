"""Unit test for recognition-attempt auditing."""

from app.services.audit_service import log_recognition_attempt


class _FakeSession:
    def __init__(self):
        self.added = None
        self.committed = False

    def add(self, value):
        self.added = value

    def commit(self):
        self.committed = True

    def refresh(self, value):
        return None


def test_recognition_attempt_is_audited_with_tenant_and_context():
    db = _FakeSession()

    audit = log_recognition_attempt(
        db,
        tenant_id="tenant-a",
        tenant_member_id="member-a",
        result={
            "recognized": True,
            "employee_id": "employee-a",
            "confidence": 0.91,
            "distance": 0.09,
            "threshold": 0.45,
            "recognition_status": "MATCHED",
        },
        camera_id="camera-a",
        mode="attendance",
    )

    assert db.committed is True
    assert audit.tenant_id == "tenant-a"
    assert audit.tenant_member_id == "member-a"
    assert audit.entity_id == "employee-a"
    assert audit.details["recognition_status"] == "MATCHED"
    assert audit.details["camera_id"] == "camera-a"

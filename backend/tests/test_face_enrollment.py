"""Integration tests for real-vector face enrollment behavior."""

from __future__ import annotations

import pytest

from app.models.employee import EmployeeFaceEmbedding
from app.services.face_ai_service import (
    MULTIPLE_FACES_DETECTED,
    NO_FACE_DETECTED,
    FaceAnalysisResult,
    FaceValidationError,
)

pytestmark = pytest.mark.integration

BASE = "/api/client-admin/attendance"


def _create_employee(client, headers, code: str):
    response = client.post(
        f"{BASE}/employees",
        headers=headers,
        json={
            "employee_code": code,
            "full_name": f"Employee {code}",
            "email": f"{code.lower()}@example.test",
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _files():
    return [
        ("files", (f"face-{index}.jpg", b"server-owned-image-bytes", "image/jpeg"))
        for index in range(3)
    ]


def _analysis() -> FaceAnalysisResult:
    return FaceAnalysisResult(
        embedding=[1.0, *([0.0] * 511)],
        detection_confidence=0.99,
        quality_score=0.95,
        width=640,
        height=480,
        face_count=1,
        face_bbox=(120, 60, 500, 440),
        face_size_px=380,
        blur_score=500.0,
        brightness=125.0,
    )


def _enroll(client, headers, employee_id: str):
    return client.post(
        f"{BASE}/employees/{employee_id}/face-images",
        headers=headers,
        files=_files(),
    )


def test_successful_enrollment_stores_normalized_pgvector(
    client,
    db,
    tenant_admin_headers,
    monkeypatch,
):
    monkeypatch.setattr("app.services.employee_service.analyze_face_image", lambda *args, **kwargs: _analysis())
    employee = _create_employee(client, tenant_admin_headers, "FACE-001")

    response = _enroll(client, tenant_admin_headers, employee["id"])

    assert response.status_code == 201, response.text
    assert response.json()["profile"]["enrollment_status"] == "Enrolled"
    assert {item["status"] for item in response.json()["validation_results"]} == {"Validated"}
    assert {item["enrollment_status"] for item in response.json()["validation_results"]} == {"valid"}
    embeddings = db.query(EmployeeFaceEmbedding).filter(
        EmployeeFaceEmbedding.tenant_id == employee["tenant_id"],
        EmployeeFaceEmbedding.employee_id == employee["id"],
    ).all()
    assert len(embeddings) == 3
    assert sum(value * value for value in embeddings[0].embedding) == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("code", "message"),
    [
        (NO_FACE_DETECTED, "No face was detected."),
        (MULTIPLE_FACES_DETECTED, "Multiple faces were detected."),
    ],
)
def test_invalid_face_detection_is_rejected(
    client,
    tenant_admin_headers,
    monkeypatch,
    code,
    message,
):
    def reject(*args, **kwargs):
        raise FaceValidationError(code, message)

    monkeypatch.setattr("app.services.employee_service.analyze_face_image", reject)
    employee = _create_employee(client, tenant_admin_headers, f"BAD-{code[:5]}")

    response = _enroll(client, tenant_admin_headers, employee["id"])

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == code
    assert {item["status"] for item in response.json()["detail"]["validation_results"]} == {"Failed"}
    assert {
        item["enrollment_status"] for item in response.json()["detail"]["validation_results"]
    } == {"rejected"}


def test_duplicate_face_is_rejected_inside_same_tenant(
    client,
    tenant_admin_headers,
    monkeypatch,
):
    monkeypatch.setattr("app.services.employee_service.analyze_face_image", lambda *args, **kwargs: _analysis())
    first = _create_employee(client, tenant_admin_headers, "DUP-001")
    second = _create_employee(client, tenant_admin_headers, "DUP-002")
    assert _enroll(client, tenant_admin_headers, first["id"]).status_code == 201

    response = _enroll(client, tenant_admin_headers, second["id"])

    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail["code"] == "DUPLICATE_FACE_DETECTED"
    assert {item["status"] for item in detail["validation_results"]} == {"Rejected"}
    assert {item["enrollment_status"] for item in detail["validation_results"]} == {"rejected"}
    assert {
        item["duplicate_employee_id"] for item in detail["validation_results"]
    } == {first["id"]}


def test_same_face_is_allowed_in_another_tenant(
    client,
    tenant_admin_headers,
    super_admin_headers,
    monkeypatch,
):
    monkeypatch.setattr("app.services.employee_service.analyze_face_image", lambda *args, **kwargs: _analysis())
    tenant_a_employee = _create_employee(client, tenant_admin_headers, "TENANT-A-FACE")
    assert _enroll(client, tenant_admin_headers, tenant_a_employee["id"]).status_code == 201

    created_tenant = client.post(
        "/api/admin/tenants",
        headers=super_admin_headers,
        json={
            "full_name": "Face Tenant Admin",
            "email": "face-tenant-admin@example.test",
            "password": "TenantFace@123",
            "organization_name": "Face Tenant",
            "slug": "face-tenant",
            "status": "active",
            "enabled_modules": ["attendance"],
        },
    )
    assert created_tenant.status_code == 201, created_tenant.text
    login = client.post(
        "/api/tenant/auth/login",
        json={
            "email": "face-tenant-admin@example.test",
            "password": "TenantFace@123",
        },
    )
    assert login.status_code == 200, login.text
    tenant_b_headers = {
        "Authorization": f"Bearer {login.json()['token']['access_token']}"
    }
    tenant_b_employee = _create_employee(client, tenant_b_headers, "TENANT-B-FACE")

    response = _enroll(client, tenant_b_headers, tenant_b_employee["id"])

    assert response.status_code == 201, response.text
    assert response.json()["profile"]["enrollment_status"] == "Enrolled"

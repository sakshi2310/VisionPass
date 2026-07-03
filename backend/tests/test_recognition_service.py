"""Unit tests for tenant-scoped face recognition."""

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.models.alert import Alert
from app.services.face_ai_service import (
    LOW_FACE_CONFIDENCE,
    MULTIPLE_FACES_DETECTED,
    NO_FACE_DETECTED,
    FaceAnalysisResult,
    FaceValidationError,
)
from app.services.recognition_service import recognize_employee_face


class _FakeResult:
    def __init__(self, row):
        self.row = row

    def mappings(self):
        return self

    def first(self):
        return self.row


class _FakeSession:
    def __init__(self, row=None):
        self.row = row
        self.statement = None
        self.parameters = None
        self.added = []

    def execute(self, statement, parameters):
        self.statement = statement
        self.parameters = parameters
        return _FakeResult(self.row)

    def add(self, value):
        self.added.append(value)


@pytest.fixture()
def face_settings():
    return SimpleNamespace(
        min_resolution_width=320,
        min_resolution_height=240,
        min_face_size_px=64,
        max_blur_score=120.0,
        min_brightness=35.0,
        max_brightness=220.0,
    )


@pytest.fixture()
def analysis():
    return FaceAnalysisResult(
        embedding=[1.0, *([0.0] * 511)],
        detection_confidence=0.99,
        quality_score=0.95,
        width=640,
        height=480,
        face_count=1,
        face_bbox=(100, 60, 500, 440),
        face_size_px=380,
        blur_score=500.0,
        brightness=125.0,
    )


def _patch_analysis(monkeypatch, face_settings, value):
    monkeypatch.setattr(
        "app.services.recognition_service.get_or_create_face_settings",
        lambda db, tenant_id: face_settings,
    )
    if isinstance(value, Exception):
        def raise_validation(*args, **kwargs):
            raise value

        monkeypatch.setattr(
            "app.services.recognition_service.analyze_face_image",
            raise_validation,
        )
    else:
        monkeypatch.setattr(
            "app.services.recognition_service.analyze_face_image",
            lambda *args, **kwargs: value,
        )


def test_matched_employee(monkeypatch, face_settings, analysis):
    _patch_analysis(monkeypatch, face_settings, analysis)
    db = _FakeSession(
        {
            "employee_id": "employee-1",
            "employee_name": "Matched Employee",
            "distance": 0.08,
            "confidence": 0.92,
        }
    )

    result = recognize_employee_face(db, "tenant-a", b"image")

    assert result["recognized"] is True
    assert result["recognition_status"] == "MATCHED"
    assert result["employee_id"] == "employee-1"
    assert result["confidence"] == pytest.approx(0.92)
    assert result["threshold"] == settings.face_recognition_threshold


def test_unknown_face_when_tenant_has_no_enrollments(monkeypatch, face_settings, analysis):
    _patch_analysis(monkeypatch, face_settings, analysis)
    db = _FakeSession(None)
    result = recognize_employee_face(db, "tenant-a", b"image")

    assert result["recognized"] is False
    assert result["recognition_status"] == "UNKNOWN"
    assert result["employee_id"] is None
    assert result["confidence"] is None
    assert len(db.added) == 1
    assert isinstance(db.added[0], Alert)
    assert db.added[0].alert_type == "UNKNOWN_FACE"


def test_nearest_match_below_threshold_is_low_confidence(monkeypatch, face_settings, analysis):
    _patch_analysis(monkeypatch, face_settings, analysis)
    db = _FakeSession(
        {
            "employee_id": "nearest-employee",
            "employee_name": "Nearest Employee",
            "distance": 0.80,
            "confidence": 0.20,
        }
    )

    result = recognize_employee_face(db, "tenant-a", b"image")

    assert result["recognized"] is False
    assert result["recognition_status"] == "LOW_CONFIDENCE"
    assert result["employee_id"] is None
    assert result["confidence"] == pytest.approx(0.20)
    assert db.added[0].alert_type == "LOW_CONFIDENCE_FACE"


def test_low_detection_confidence(monkeypatch, face_settings):
    _patch_analysis(
        monkeypatch,
        face_settings,
        FaceValidationError(
            LOW_FACE_CONFIDENCE,
            "Low confidence",
            detection_confidence=0.25,
        ),
    )

    result = recognize_employee_face(_FakeSession(), "tenant-a", b"image")

    assert result["recognized"] is False
    assert result["recognition_status"] == "LOW_CONFIDENCE"
    assert result["confidence"] == pytest.approx(0.25)


@pytest.mark.parametrize(
    ("error_code", "expected_status"),
    [
        (NO_FACE_DETECTED, "NO_FACE"),
        (MULTIPLE_FACES_DETECTED, "MULTIPLE_FACES"),
    ],
)
def test_face_count_errors(monkeypatch, face_settings, error_code, expected_status):
    _patch_analysis(
        monkeypatch,
        face_settings,
        FaceValidationError(error_code, expected_status),
    )

    result = recognize_employee_face(_FakeSession(), "tenant-a", b"image")

    assert result["recognized"] is False
    assert result["recognition_status"] == expected_status


def test_nearest_neighbor_query_is_tenant_isolated(monkeypatch, face_settings, analysis):
    _patch_analysis(monkeypatch, face_settings, analysis)
    db = _FakeSession(None)

    result = recognize_employee_face(db, "tenant-b", b"image")

    assert result["recognition_status"] == "UNKNOWN"
    assert db.parameters["tenant_id"] == "tenant-b"
    assert "face.tenant_id = :tenant_id" in str(db.statement)
    assert "employee.tenant_id = face.tenant_id" in str(db.statement)

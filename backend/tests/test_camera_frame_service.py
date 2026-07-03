"""Unit tests for live camera frame processing."""

from types import SimpleNamespace

import pytest

from app.core.config import settings
from app.models.camera import CameraEvent
from app.services.camera_frame_service import process_camera_frame
from app.services.camera_service import CameraError


class _FakeSession:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)

    def commit(self):
        return None

    def refresh(self, value):
        return None


def _camera():
    return SimpleNamespace(id="camera-a", tenant_id="tenant-a", is_active=True)


def _snapshot():
    return {
        "content": b"validated-frame",
        "content_type": "image/jpeg",
        "width": 640,
        "height": 480,
    }


def _patch_camera(monkeypatch, *, camera=None):
    selected = _camera() if camera is None else camera
    monkeypatch.setattr(
        "app.services.camera_frame_service.get_camera",
        lambda db, tenant_id, camera_id: selected,
    )
    monkeypatch.setattr(
        "app.services.camera_frame_service.fetch_snapshot",
        lambda db, camera: _snapshot(),
    )


def test_process_camera_frame(monkeypatch):
    _patch_camera(monkeypatch)
    db = _FakeSession()

    result = process_camera_frame(
        db,
        "tenant-a",
        "camera-a",
        recognize=False,
    )

    assert result["recognition"] is None
    assert result["camera_event"].recognition_status == "FRAME_CAPTURED"
    assert result["frame"]["frame_interval_seconds"] == settings.camera_frame_interval_seconds
    assert any(isinstance(item, CameraEvent) for item in db.added)


def test_unknown_face_is_logged(monkeypatch):
    _patch_camera(monkeypatch)
    monkeypatch.setattr(
        "app.services.camera_frame_service.recognize_employee_face",
        lambda db, tenant_id, content: {
            "recognized": False,
            "employee_id": None,
            "employee_name": None,
            "confidence": 0.2,
            "distance": 0.8,
            "threshold": settings.face_recognition_threshold,
            "recognition_status": "UNKNOWN",
        },
    )

    result = process_camera_frame(_FakeSession(), "tenant-a", "camera-a", recognize=True)

    assert result["recognition"]["recognized"] is False
    assert result["camera_event"].recognition_status == "UNKNOWN"


def test_matched_face_is_logged(monkeypatch):
    _patch_camera(monkeypatch)
    monkeypatch.setattr(
        "app.services.camera_frame_service.recognize_employee_face",
        lambda db, tenant_id, content: {
            "recognized": True,
            "employee_id": "employee-a",
            "employee_name": "Employee A",
            "confidence": 0.94,
            "distance": 0.06,
            "threshold": settings.face_recognition_threshold,
            "recognition_status": "MATCHED",
        },
    )

    result = process_camera_frame(_FakeSession(), "tenant-a", "camera-a", recognize=True)

    assert result["recognition"]["employee_id"] == "employee-a"
    assert result["camera_event"].employee_id == "employee-a"
    assert result["camera_event"].confidence == pytest.approx(0.94)


def test_camera_offline_is_logged(monkeypatch):
    _patch_camera(monkeypatch)

    def offline(db, camera):
        raise CameraError("CAMERA_OFFLINE", "Camera could not be reached.", status_code=502)

    monkeypatch.setattr("app.services.camera_frame_service.fetch_snapshot", offline)
    db = _FakeSession()

    with pytest.raises(CameraError) as error:
        process_camera_frame(db, "tenant-a", "camera-a", recognize=True)

    assert error.value.code == "CAMERA_OFFLINE"
    events = [item for item in db.added if isinstance(item, CameraEvent)]
    assert events[-1].recognition_status == "CAMERA_OFFLINE"


def test_camera_lookup_is_tenant_isolated(monkeypatch):
    calls = []

    def no_camera(db, tenant_id, camera_id):
        calls.append((tenant_id, camera_id))
        return None

    monkeypatch.setattr("app.services.camera_frame_service.get_camera", no_camera)

    with pytest.raises(CameraError) as error:
        process_camera_frame(_FakeSession(), "tenant-b", "camera-a", recognize=True)

    assert error.value.code == "CAMERA_NOT_FOUND"
    assert calls == [("tenant-b", "camera-a")]

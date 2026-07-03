"""Unit tests for IP camera snapshot validation."""

from types import SimpleNamespace

import cv2
import httpx
import numpy as np
import pytest

from app.core.config import settings
from app.models.alert import Alert
from app.services.camera_service import CameraError, fetch_snapshot


class _FakeSession:
    def __init__(self):
        self.values = []

    def add(self, value):
        self.values.append(value)

    def commit(self):
        return None

    def refresh(self, value):
        return None


def _camera():
    return SimpleNamespace(
        id="camera-a",
        tenant_id="tenant-a",
        snapshot_url="http://camera.local/shot.jpg",
        username=None,
        password_encrypted=None,
        health_status="unknown",
        last_seen_at=None,
    )


def _jpeg() -> bytes:
    success, encoded = cv2.imencode(".jpg", np.full((240, 320, 3), 120, dtype=np.uint8))
    assert success
    return encoded.tobytes()


def _patch_client(monkeypatch, handler):
    captured = {}
    original_client = httpx.Client

    def client_factory(**kwargs):
        captured.update(kwargs)
        return original_client(transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr("app.services.camera_service.httpx.Client", client_factory)
    return captured


def test_snapshot_success_sets_camera_online(monkeypatch):
    captured = _patch_client(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            content=_jpeg(),
            headers={"content-type": "image/jpeg"},
        ),
    )
    camera = _camera()

    result = fetch_snapshot(_FakeSession(), camera)

    assert result["width"] == 320
    assert result["height"] == 240
    assert camera.health_status == "online"
    assert camera.last_seen_at is not None
    assert captured["timeout"] == settings.camera_request_timeout_seconds


def test_snapshot_failure_sets_camera_error(monkeypatch):
    _patch_client(
        monkeypatch,
        lambda request: httpx.Response(
            200,
            content=b"not-an-image",
            headers={"content-type": "text/plain"},
        ),
    )
    camera = _camera()

    db = _FakeSession()
    with pytest.raises(CameraError) as error:
        fetch_snapshot(db, camera)

    assert error.value.code == "INVALID_SNAPSHOT"
    assert camera.health_status == "error"
    alerts = [value for value in db.values if isinstance(value, Alert)]
    assert len(alerts) == 1
    assert alerts[0].alert_type == "CAMERA_ERROR"


def test_camera_offline_creates_alert(monkeypatch):
    def offline(request):
        raise httpx.ConnectError("offline", request=request)

    _patch_client(monkeypatch, offline)
    camera = _camera()
    db = _FakeSession()

    with pytest.raises(CameraError) as error:
        fetch_snapshot(db, camera)

    assert error.value.code == "CAMERA_OFFLINE"
    assert camera.health_status == "offline"
    alerts = [value for value in db.values if isinstance(value, Alert)]
    assert len(alerts) == 1
    assert alerts[0].alert_type == "CAMERA_OFFLINE"

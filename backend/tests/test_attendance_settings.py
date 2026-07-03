"""Attendance settings integration tests."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration

BASE = "/api/client-admin/attendance/settings"


def test_read_and_update_attendance_settings(client, tenant_admin_headers):
    initial = client.get(BASE, headers=tenant_admin_headers)
    assert initial.status_code == 200, initial.text
    assert initial.json()["attendance_settings"]["timezone"] == "Asia/Kolkata"
    assert len(initial.json()["working_days"]) == 7

    updated = client.put(
        BASE,
        headers=tenant_admin_headers,
        json={
            "duplicate_detection_cooldown_minutes": 8,
            "allow_manual_correction": False,
            "require_correction_reason": True,
            "timezone": "Asia/Calcutta",
            "working_days": [0, 1, 2, 3, 4],
        },
    )
    assert updated.status_code == 200, updated.text
    body = updated.json()
    assert body["attendance_settings"]["duplicate_detection_cooldown_minutes"] == 8
    assert body["attendance_settings"]["allow_manual_correction"] is False
    assert [
        day["day_of_week"] for day in body["working_days"] if day["is_working"]
    ] == [0, 1, 2, 3, 4]


def test_attendance_settings_validate_working_days(client, tenant_admin_headers):
    response = client.put(
        BASE,
        headers=tenant_admin_headers,
        json={
            "duplicate_detection_cooldown_minutes": 5,
            "allow_manual_correction": True,
            "require_correction_reason": True,
            "timezone": "Asia/Kolkata",
            "working_days": [],
        },
    )
    assert response.status_code == 422

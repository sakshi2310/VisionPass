"""Integration tests for the attendance board projection."""

from __future__ import annotations

import logging

import pytest


pytestmark = pytest.mark.integration

ADMIN_BASE = "/api/client-admin/attendance"
ATTENDANCE_BASE = "/api/attendance"


def _create_shift(client, headers):
    response = client.post(
        f"{ADMIN_BASE}/shifts",
        headers=headers,
        json={
            "name": "Day Shift",
            "start_time": "09:00:00",
            "end_time": "18:00:00",
            "grace_period_minutes": 0,
            "late_after_minutes": 0,
            "half_day_min_minutes": 240,
            "full_day_min_minutes": 480,
            "break_duration_minutes": 0,
            "is_default": True,
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_employee(client, headers, code: str, shift_id: str | None = None):
    response = client.post(
        f"{ADMIN_BASE}/employees",
        headers=headers,
        json={
            "employee_code": code,
            "full_name": f"Employee {code}",
            "email": f"{code.lower()}@attendance-board.test",
            "shift_id": shift_id,
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_attendance_board_returns_projection_sections_and_logs(
    client,
    tenant_admin_headers,
    caplog,
):
    caplog.set_level(logging.INFO)
    shift = _create_shift(client, tenant_admin_headers)
    present = _create_employee(client, tenant_admin_headers, "BOARD-001", shift["id"])
    _create_employee(client, tenant_admin_headers, "BOARD-002", shift["id"])

    marked = client.post(
        f"{ATTENDANCE_BASE}/check-in",
        headers=tenant_admin_headers,
        json={
            "employee_id": present["id"],
            "source": "manual",
            "event_time": "2026-07-01T03:30:00Z",
        },
    )
    assert marked.status_code == 201, marked.text

    board = client.get(
        f"{ADMIN_BASE}/board?date=2026-07-01",
        headers=tenant_admin_headers,
    )
    assert board.status_code == 200, board.text

    body = board.json()
    assert "present_employees" in body
    assert "absent_employees" in body
    assert "latest_sessions" in body
    assert "debug_summary" in body
    assert len(body["present_employees"]) == 1
    assert len(body["absent_employees"]) == 1
    assert body["present_employees"][0]["employee_code"] == "BOARD-001"
    assert body["absent_employees"][0]["employee_code"] == "BOARD-002"
    assert body["absent_employees"][0]["reason"] == "Absent after attendance cutoff."
    assert body["debug_summary"]["present_count"] == 1
    assert body["debug_summary"]["absent_count"] == 1
    assert body["debug_summary"]["total_active_employees"] == 2
    assert body["debug_summary"]["camera_enabled"] in {True, False}

    assert any("[ATTENDANCE_EVENT]" in record.message for record in caplog.records)
    assert any("[ATTENDANCE_BOARD]" in record.message for record in caplog.records)

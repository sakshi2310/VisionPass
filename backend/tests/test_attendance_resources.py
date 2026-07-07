"""Shift, holiday, and employee API integration tests."""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration

BASE = "/api/client-admin/attendance"


def test_shift_crud(client, tenant_admin_headers):
    created = client.post(
        f"{BASE}/shifts",
        headers=tenant_admin_headers,
        json={
            "name": "Morning",
            "start_time": "08:30:00",
            "end_time": "17:30:00",
            "grace_period_minutes": 10,
            "late_after_minutes": 15,
            "half_day_min_minutes": 240,
            "full_day_min_minutes": 480,
            "auto_checkout_time": "19:00:00",
            "break_duration_minutes": 30,
            "is_default": False,
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    shift_id = created.json()["id"]

    listed = client.get(f"{BASE}/shifts", headers=tenant_admin_headers)
    assert listed.status_code == 200
    assert [shift["id"] for shift in listed.json()["shifts"]] == [shift_id]

    updated = client.put(
        f"{BASE}/shifts/{shift_id}",
        headers=tenant_admin_headers,
        json={"name": "Morning Updated", "grace_period_minutes": 12},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["name"] == "Morning Updated"

    made_default = client.patch(
        f"{BASE}/shifts/{shift_id}/default",
        headers=tenant_admin_headers,
    )
    assert made_default.status_code == 200
    assert made_default.json()["is_default"] is True

    deleted = client.delete(
        f"{BASE}/shifts/{shift_id}",
        headers=tenant_admin_headers,
    )
    assert deleted.status_code == 204
    assert (
        client.get(f"{BASE}/shifts/{shift_id}", headers=tenant_admin_headers).status_code
        == 404
    )


def test_holiday_crud(client, tenant_admin_headers):
    created = client.post(
        f"{BASE}/holidays",
        headers=tenant_admin_headers,
        json={
            "holiday_name": "Founders Day",
            "holiday_date": "2027-01-15",
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    holiday_id = created.json()["id"]

    listed = client.get(f"{BASE}/holidays", headers=tenant_admin_headers)
    assert listed.status_code == 200
    assert [holiday["id"] for holiday in listed.json()["holidays"]] == [holiday_id]

    updated = client.put(
        f"{BASE}/holidays/{holiday_id}",
        headers=tenant_admin_headers,
        json={"holiday_name": "Vision Pass Day", "is_active": False},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["holiday_name"] == "Vision Pass Day"
    assert updated.json()["is_active"] is False

    deleted = client.delete(
        f"{BASE}/holidays/{holiday_id}",
        headers=tenant_admin_headers,
    )
    assert deleted.status_code == 204
    assert client.get(f"{BASE}/holidays", headers=tenant_admin_headers).json()[
        "holidays"
    ] == []


def test_employee_crud(client, tenant_admin_headers):
    created = client.post(
        f"{BASE}/employees",
        headers=tenant_admin_headers,
        json={
            "employee_code": "VP-100",
            "full_name": "Vision Pass Employee",
            "email": "employee100@example.test",
            "mobile": "9999999999",
            "department": "Security",
            "designation": "Supervisor",
            "joining_date": "2026-07-01",
            "employee_type": "Full Time",
            "is_active": True,
        },
    )
    assert created.status_code == 201, created.text
    employee_id = created.json()["id"]

    listed = client.get(f"{BASE}/employees", headers=tenant_admin_headers)
    assert listed.status_code == 200
    assert [employee["id"] for employee in listed.json()["employees"]] == [employee_id]

    fetched = client.get(
        f"{BASE}/employees/{employee_id}",
        headers=tenant_admin_headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["tenant_id"] == created.json()["tenant_id"]

    updated = client.put(
        f"{BASE}/employees/{employee_id}",
        headers=tenant_admin_headers,
        json={"designation": "Senior Supervisor", "mobile": "8888888888"},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["designation"] == "Senior Supervisor"

    deactivated = client.patch(
        f"{BASE}/employees/{employee_id}/deactivate",
        headers=tenant_admin_headers,
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    activated = client.patch(
        f"{BASE}/employees/{employee_id}/activate",
        headers=tenant_admin_headers,
    )
    assert activated.status_code == 200
    assert activated.json()["is_active"] is True

    deleted = client.delete(
        f"{BASE}/employees/{employee_id}",
        headers=tenant_admin_headers,
    )
    assert deleted.status_code == 204
    assert (
        client.get(
            f"{BASE}/employees/{employee_id}",
            headers=tenant_admin_headers,
        ).status_code
        == 404
    )


def test_employee_code_is_generated_when_omitted(client, tenant_admin_headers):
    created = client.post(
        f"{BASE}/employees",
        headers=tenant_admin_headers,
        json={
            "full_name": "Generated Code Employee",
            "email": "generated-code@example.test",
        },
    )

    assert created.status_code == 201, created.text
    assert created.json()["employee_code"].startswith("EMP-")

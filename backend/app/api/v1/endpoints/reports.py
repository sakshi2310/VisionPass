"""Tenant-isolated operational reports and CSV exports."""

from __future__ import annotations

import csv
import io
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.services import report_service

router = APIRouter()


def _validate_range(start_date: date | None, end_date: date | None) -> None:
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be on or before end_date",
        )


def _result(items: list[dict]) -> dict:
    return {"items": items, "total": len(items)}


def _csv_response(items: list[dict], filename: str, columns: list[str]) -> StreamingResponse:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(items)
    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@router.get("/attendance")
def read_attendance_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.attendance_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
        camera_id=camera_id, event_type=event_type,
    ))


@router.get("/employees")
def read_employee_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.employee_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
    ))


@router.get("/visitors")
def read_visitor_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.visitor_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, status=status, camera_id=camera_id,
    ))


@router.get("/cameras")
def read_camera_report(
    start_date: date | None = None,
    end_date: date | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.camera_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        status=status, camera_id=camera_id, event_type=event_type,
    ))


@router.get("/recognition")
def read_recognition_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.recognition_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
        camera_id=camera_id, event_type=event_type,
    ))


@router.get("/access")
def read_access_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    return _result(report_service.access_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
        camera_id=camera_id, event_type=event_type,
    ))


@router.get("/attendance/export.csv")
def export_attendance_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    items = report_service.attendance_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
        camera_id=camera_id, event_type=event_type,
    )
    return _csv_response(items, "attendance-report.csv", [
        "attendance_date", "employee_code", "employee_name", "department", "status",
        "first_check_in", "last_check_out", "total_work_minutes",
    ])


@router.get("/access/export.csv")
def export_access_report(
    start_date: date | None = None,
    end_date: date | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    status: str | None = None,
    camera_id: str | None = None,
    event_type: str | None = None,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    _validate_range(start_date, end_date)
    items = report_service.access_report(
        db, current_admin.tenant_id, start_date=start_date, end_date=end_date,
        employee_id=employee_id, department=department, status=status,
        camera_id=camera_id, event_type=event_type,
    )
    return _csv_response(items, "access-report.csv", [
        "created_at", "identity_type", "identity_name", "department", "camera_name",
        "decision", "reason", "confidence",
    ])

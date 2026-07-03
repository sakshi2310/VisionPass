"""Authenticated tenant-user self-service API."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, require_role
from app.schemas.me import (
    MeAttendanceResponse,
    MeDashboardResponse,
    MeNotificationsResponse,
    MeProfileResponse,
)
from app.services.me_service import (
    get_me_attendance,
    get_me_dashboard,
    get_me_notifications,
    get_me_profile,
)

router = APIRouter()


@router.get("/dashboard", response_model=MeDashboardResponse)
def read_me_dashboard(
    db: Session = Depends(database_session),
    current_user=Depends(require_role(["user"])),
) -> MeDashboardResponse:
    return MeDashboardResponse(**get_me_dashboard(db, current_user))


@router.get("/attendance", response_model=MeAttendanceResponse)
def read_me_attendance(
    month: str | None = Query(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$"),
    db: Session = Depends(database_session),
    current_user=Depends(require_role(["user"])),
) -> MeAttendanceResponse:
    try:
        return MeAttendanceResponse(**get_me_attendance(db, current_user, month))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.get("/profile", response_model=MeProfileResponse)
def read_me_profile(
    db: Session = Depends(database_session),
    current_user=Depends(require_role(["user"])),
) -> MeProfileResponse:
    return MeProfileResponse(**get_me_profile(db, current_user))


@router.get("/notifications", response_model=MeNotificationsResponse)
def read_me_notifications(
    db: Session = Depends(database_session),
    current_user=Depends(require_role(["user"])),
) -> MeNotificationsResponse:
    return MeNotificationsResponse(notifications=get_me_notifications(db, current_user))

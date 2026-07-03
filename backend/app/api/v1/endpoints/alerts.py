"""Client-admin alert lifecycle routes."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.schemas.alert import AlertListResponse, AlertRead
from app.services.alert_service import (
    AlertError,
    acknowledge_alert,
    get_alert,
    list_alerts,
    resolve_alert,
)

router = APIRouter()


@router.get("", response_model=AlertListResponse)
def read_alerts(
    status_filter: Literal["open", "acknowledged", "resolved"] | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AlertListResponse:
    return AlertListResponse(
        alerts=[
            AlertRead.model_validate(alert)
            for alert in list_alerts(
                db,
                current_admin.tenant_id,
                status=status_filter,
                limit=limit,
            )
        ]
    )


@router.get("/{alert_id}", response_model=AlertRead)
def read_alert(
    alert_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AlertRead:
    alert = get_alert(db, current_admin.tenant_id, alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)


def _change_status(action, db: Session, tenant_id: str, alert_id: str) -> AlertRead:
    try:
        alert = action(db, tenant_id, alert_id)
    except AlertError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    return AlertRead.model_validate(alert)


@router.post("/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge(
    alert_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AlertRead:
    return _change_status(acknowledge_alert, db, current_admin.tenant_id, alert_id)


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve(
    alert_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AlertRead:
    return _change_status(resolve_alert, db, current_admin.tenant_id, alert_id)

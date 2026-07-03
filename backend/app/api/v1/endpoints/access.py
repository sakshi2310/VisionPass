"""Client-admin access decision routes."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.schemas.access_event import (
    AccessDecisionRequest,
    AccessDecisionResponse,
    AccessLogListResponse,
    AccessLogRead,
)
from app.services.access_service import decide_access, list_access_logs

router = APIRouter()


def _log_read(log, *, identity_name: str | None = None, camera_name: str | None = None) -> AccessLogRead:
    values = AccessLogRead.model_validate(log).model_dump()
    values["identity_name"] = identity_name
    values["camera_name"] = camera_name
    return AccessLogRead(**values)


@router.post("/decision", response_model=AccessDecisionResponse)
def create_access_decision(
    payload: AccessDecisionRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AccessDecisionResponse:
    if payload.tenant_id != current_admin.tenant_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant scope mismatch")
    try:
        log = decide_access(
            db,
            current_admin.tenant_id,
            employee_id=payload.employee_id,
            visitor_id=payload.visitor_id,
            camera_id=payload.camera_id,
            confidence=payload.confidence,
            recognition_status=payload.recognition_status,
            timestamp=payload.timestamp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return AccessDecisionResponse(
        decision=log.decision,
        reason=log.reason,
        log=_log_read(log),
    )


@router.get("/logs", response_model=AccessLogListResponse)
def read_access_logs(
    decision: Literal["granted", "denied", "manual_review"] | None = None,
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> AccessLogListResponse:
    rows = list_access_logs(
        db,
        current_admin.tenant_id,
        decision=decision,
        limit=limit,
    )
    return AccessLogListResponse(
        logs=[
            _log_read(
                row["log"],
                identity_name=row["identity_name"],
                camera_name=row["camera_name"],
            )
            for row in rows
        ]
    )

"""Client-admin visitor management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.schemas.visitor import (
    VisitorCheckIn,
    VisitorCheckOut,
    VisitorCreate,
    VisitorDetail,
    VisitorListResponse,
    VisitorRead,
    VisitorUpdate,
    VisitorVisitActionResponse,
    VisitorVisitRead,
)
from app.services.visitor_service import (
    VisitorError,
    check_in_visitor,
    check_out_visitor,
    create_visitor,
    delete_visitor,
    get_visitor,
    list_visitor_visits,
    list_visitors,
    update_visitor,
)

router = APIRouter()


def _raise_visitor_error(exc: VisitorError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=VisitorListResponse)
def read_visitors(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorListResponse:
    return VisitorListResponse(
        visitors=[VisitorRead.model_validate(visitor) for visitor in list_visitors(db, current_admin.tenant_id)]
    )


@router.post("", response_model=VisitorRead, status_code=status.HTTP_201_CREATED)
def add_visitor(
    payload: VisitorCreate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorRead:
    try:
        visitor = create_visitor(
            db,
            current_admin.tenant_id,
            current_admin.id,
            payload.model_dump(),
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    return VisitorRead.model_validate(visitor)


@router.get("/{visitor_id}", response_model=VisitorDetail)
def read_visitor(
    visitor_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorDetail:
    visitor = get_visitor(db, current_admin.tenant_id, visitor_id)
    if visitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")
    visits = list_visitor_visits(db, current_admin.tenant_id, visitor.id)
    return VisitorDetail(
        **VisitorRead.model_validate(visitor).model_dump(),
        visits=[VisitorVisitRead.model_validate(visit) for visit in visits],
    )


@router.put("/{visitor_id}", response_model=VisitorRead)
def save_visitor(
    visitor_id: str,
    payload: VisitorUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorRead:
    try:
        visitor = update_visitor(
            db,
            current_admin.tenant_id,
            visitor_id,
            current_admin.id,
            payload.model_dump(exclude_unset=True),
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    if visitor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")
    return VisitorRead.model_validate(visitor)


@router.delete("/{visitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_visitor(
    visitor_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    if not delete_visitor(db, current_admin.tenant_id, visitor_id, current_admin.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")


@router.post("/{visitor_id}/check-in", response_model=VisitorVisitActionResponse)
def check_in(
    visitor_id: str,
    payload: VisitorCheckIn,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorVisitActionResponse:
    try:
        result = check_in_visitor(
            db,
            current_admin.tenant_id,
            visitor_id,
            current_admin.id,
            access_status=payload.access_status,
            notes=payload.notes,
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")
    visitor, visit = result
    return VisitorVisitActionResponse(
        visitor=VisitorRead.model_validate(visitor),
        visit=VisitorVisitRead.model_validate(visit),
    )


@router.post("/{visitor_id}/check-out", response_model=VisitorVisitActionResponse)
def check_out(
    visitor_id: str,
    payload: VisitorCheckOut,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> VisitorVisitActionResponse:
    try:
        result = check_out_visitor(
            db,
            current_admin.tenant_id,
            visitor_id,
            current_admin.id,
            notes=payload.notes,
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visitor not found")
    visitor, visit = result
    return VisitorVisitActionResponse(
        visitor=VisitorRead.model_validate(visitor),
        visit=VisitorVisitRead.model_validate(visit),
    )

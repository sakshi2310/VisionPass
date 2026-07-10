"""Client-admin unknown review routes."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin, require_module
from app.schemas.person_detection import (
    PersonDetectionAddVisitorRequest,
    PersonDetectionDetailResponse,
    PersonDetectionListResponse,
    PersonDetectionNoteRequest,
    PersonDetectionRead,
)
from app.schemas.person_detection import PersonDetectionAddVisitorResponse
from app.schemas.visitor import VisitorRead, VisitorVisitRead
from app.services.person_detection_service import (
    add_note_to_person_detection,
    add_visitor_from_person_detection,
    get_person_detection,
    ignore_person_detection,
    list_unknown_review_detections,
    mark_person_detection_reviewed,
    mark_person_detection_suspicious,
)
from app.services.visitor_service import VisitorError

router = APIRouter(dependencies=[Depends(require_module("visitor_unknown"))])


def _raise_visitor_error(exc: VisitorError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=PersonDetectionListResponse)
def read_unknown_review(
    camera_id: str | None = Query(default=None),
    zone_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionListResponse:
    detections = list_unknown_review_detections(
        db,
        current_admin.tenant_id,
        camera_id=camera_id,
        zone_id=zone_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return PersonDetectionListResponse(
        detections=[PersonDetectionRead.model_validate(detection) for detection in detections]
    )


@router.patch("/{detection_id}/note", response_model=PersonDetectionDetailResponse)
def update_unknown_review_note(
    detection_id: str,
    payload: PersonDetectionNoteRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = add_note_to_person_detection(db, current_admin.tenant_id, detection_id, payload.note)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/mark-reviewed", response_model=PersonDetectionDetailResponse)
def mark_reviewed(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = mark_person_detection_reviewed(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/mark-suspicious", response_model=PersonDetectionDetailResponse)
def mark_suspicious(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = mark_person_detection_suspicious(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/ignore", response_model=PersonDetectionDetailResponse)
def ignore_unknown_review(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = ignore_person_detection(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/add-visitor", response_model=PersonDetectionAddVisitorResponse, status_code=status.HTTP_201_CREATED)
def add_unknown_as_visitor(
    detection_id: str,
    payload: PersonDetectionAddVisitorRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionAddVisitorResponse:
    try:
        result = add_visitor_from_person_detection(
            db,
            current_admin.tenant_id,
            detection_id,
            current_admin.id,
            payload.model_dump(exclude_unset=True),
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown detection not found")
    return PersonDetectionAddVisitorResponse(
        visitor=VisitorRead.model_validate(result["visitor"]),
        visit=VisitorVisitRead.model_validate(result["visit"]),
        person_detection=PersonDetectionDetailResponse.model_validate(result["person_detection"]),
    )

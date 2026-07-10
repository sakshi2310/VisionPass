"""Client-admin person detection routes."""

from pathlib import Path
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin, require_module
from app.schemas.person_detection import (
    PersonDetectionAddStaffRequest,
    PersonDetectionAddStaffResponse,
    PersonDetectionAddVisitorResponse,
    PersonDetectionAddVisitorRequest,
    PersonDetectionDetailResponse,
    PersonDetectionListResponse,
    PersonDetectionNoteRequest,
    PersonDetectionRead,
)
from app.schemas.visitor import VisitorRead, VisitorVisitRead
from app.services.person_detection_service import (
    add_note_to_person_detection,
    add_staff_from_person_detection,
    add_visitor_from_person_detection,
    get_person_detection,
    ignore_person_detection,
    list_person_detections,
)
from app.services.visitor_service import VisitorError

router = APIRouter(dependencies=[Depends(require_module("visitor_unknown"))])


def _raise_visitor_error(exc: VisitorError) -> None:
    raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.get("", response_model=PersonDetectionListResponse)
def read_person_detections(
    camera_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    match_type: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionListResponse:
    detections = list_person_detections(
        db,
        current_admin.tenant_id,
        camera_id=camera_id,
        status=status,
        match_type=match_type,
        limit=limit,
        offset=offset,
    )
    return PersonDetectionListResponse(
        detections=[PersonDetectionRead.model_validate(detection) for detection in detections]
    )


@router.get("/{detection_id}", response_model=PersonDetectionDetailResponse)
def read_person_detection(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = get_person_detection(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/note", response_model=PersonDetectionDetailResponse)
def add_person_detection_note(
    detection_id: str,
    payload: PersonDetectionNoteRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = add_note_to_person_detection(db, current_admin.tenant_id, detection_id, payload.note)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/ignore", response_model=PersonDetectionDetailResponse)
def ignore_person_detection_route(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> PersonDetectionDetailResponse:
    detection = ignore_person_detection(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    return PersonDetectionDetailResponse.model_validate(detection)


@router.post("/{detection_id}/add-visitor", response_model=PersonDetectionAddVisitorResponse, status_code=status.HTTP_201_CREATED)
def add_visitor_from_detection_route(
    detection_id: str,
    payload: PersonDetectionAddVisitorRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    return PersonDetectionAddVisitorResponse(
        visitor=VisitorRead.model_validate(result["visitor"]),
        visit=VisitorVisitRead.model_validate(result["visit"]),
        person_detection=PersonDetectionDetailResponse.model_validate(result["person_detection"]),
    )


@router.post("/{detection_id}/add-staff", response_model=PersonDetectionAddStaffResponse, status_code=status.HTTP_201_CREATED)
def add_staff_from_detection_route(
    detection_id: str,
    payload: PersonDetectionAddStaffRequest,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    try:
        result = add_staff_from_person_detection(
            db,
            current_admin.tenant_id,
            detection_id,
            current_admin.id,
            payload.model_dump(exclude_unset=True),
        )
    except VisitorError as exc:
        _raise_visitor_error(exc)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    from app.schemas.employee import EmployeeFaceProfileRead, EmployeeRead

    return PersonDetectionAddStaffResponse(
        employee=EmployeeRead.model_validate(result["employee"]),
        person_detection=PersonDetectionDetailResponse.model_validate(result["person_detection"]),
        face_profile=EmployeeFaceProfileRead.model_validate(result["face_profile"]),
    )


@router.get("/{detection_id}/photo")
def read_person_detection_photo(
    detection_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
):
    detection = get_person_detection(db, current_admin.tenant_id, detection_id)
    if detection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection not found")
    if not detection.image_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection photo not found")
    photo_path = Path(detection.image_path)
    if not photo_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Person detection photo not found")
    media_type = mimetypes.guess_type(photo_path.name)[0] or "application/octet-stream"
    return FileResponse(str(photo_path), media_type=media_type, filename=photo_path.name)

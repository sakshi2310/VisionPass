"""Tenant admin camera management routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin, require_module
from app.schemas.attendance import AttendanceEventRead, AttendanceMarkResponse, DailyAttendanceRead
from app.schemas.camera import (
    CameraCreate,
    CameraEventRead,
    CameraFrameMetadata,
    CameraFrameResponse,
    CameraListResponse,
    CameraRead,
    CameraTestResponse,
    CameraUpdate,
)
from app.schemas.recognition import RecognitionResponse
from app.services.attendance_service import AttendanceMarkError
from app.services.camera_frame_service import process_camera_frame
from app.services.camera_service import (
    CameraError,
    camera_to_dict,
    create_camera,
    delete_camera,
    fetch_snapshot,
    get_camera,
    list_cameras,
    update_camera,
)
from app.services.face_ai_service import FaceModelUnavailableError, FaceValidationError

router = APIRouter()


def _camera_read(camera) -> CameraRead:
    return CameraRead.model_validate(camera_to_dict(camera))


def _raise_camera_error(exc: CameraError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    ) from exc


def _frame_response(result: dict) -> CameraFrameResponse:
    attendance = None
    if result["attendance"] is not None:
        marked = result["attendance"]
        attendance = AttendanceMarkResponse(
            event=AttendanceEventRead.model_validate(marked["event"]),
            daily=DailyAttendanceRead.model_validate(marked["daily"]),
            employee_id=str(marked["employee"].id),
            employee_name=marked["employee"].full_name,
            employee_code=marked["employee"].employee_code,
            message=marked["message"],
        )
    return CameraFrameResponse(
        camera=_camera_read(result["camera"]),
        camera_event=CameraEventRead.model_validate(result["camera_event"]),
        frame=CameraFrameMetadata.model_validate(result["frame"]),
        recognition=(
            RecognitionResponse.model_validate(result["recognition"])
            if result["recognition"] is not None
            else None
        ),
        attendance=attendance,
    )


def _run_frame_action(
    db: Session,
    tenant_id: str,
    camera_id: str,
    *,
    recognize: bool,
    mark: bool = False,
) -> CameraFrameResponse:
    try:
        result = process_camera_frame(
            db,
            tenant_id,
            camera_id,
            recognize=recognize,
            mark=mark,
        )
    except CameraError as exc:
        _raise_camera_error(exc)
    except AttendanceMarkError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    except FaceValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    except FaceModelUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return _frame_response(result)


@router.get("", response_model=CameraListResponse)
def read_cameras(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> CameraListResponse:
    return CameraListResponse(
        cameras=[_camera_read(camera) for camera in list_cameras(db, current_admin.tenant_id)]
    )


@router.post("", response_model=CameraRead, status_code=status.HTTP_201_CREATED)
def add_camera(
    payload: CameraCreate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> CameraRead:
    try:
        camera = create_camera(db, current_admin.tenant_id, **payload.model_dump())
    except CameraError as exc:
        _raise_camera_error(exc)
    return _camera_read(camera)


@router.get("/{camera_id}", response_model=CameraRead)
def read_camera(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> CameraRead:
    camera = get_camera(db, current_admin.tenant_id, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return _camera_read(camera)


@router.put("/{camera_id}", response_model=CameraRead)
def save_camera(
    camera_id: str,
    payload: CameraUpdate,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> CameraRead:
    try:
        camera = update_camera(
            db,
            current_admin.tenant_id,
            camera_id,
            payload.model_dump(exclude_unset=True),
        )
    except CameraError as exc:
        _raise_camera_error(exc)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    return _camera_read(camera)


@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_camera(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> None:
    if not delete_camera(db, current_admin.tenant_id, camera_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")


@router.post("/{camera_id}/test", response_model=CameraTestResponse)
def test_camera(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> CameraTestResponse:
    camera = get_camera(db, current_admin.tenant_id, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    try:
        snapshot = fetch_snapshot(db, camera)
    except CameraError as exc:
        _raise_camera_error(exc)
    return CameraTestResponse(
        camera_id=camera.id,
        success=True,
        health_status=camera.health_status,
        message="Camera snapshot is reachable and valid.",
        width=snapshot["width"],
        height=snapshot["height"],
        content_type=snapshot["content_type"],
    )


@router.post("/{camera_id}/snapshot")
def camera_snapshot(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> Response:
    camera = get_camera(db, current_admin.tenant_id, camera_id)
    if camera is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
    try:
        snapshot = fetch_snapshot(db, camera)
    except CameraError as exc:
        _raise_camera_error(exc)
    return Response(
        content=snapshot["content"],
        media_type=snapshot["content_type"],
        headers={"Cache-Control": "no-store"},
    )


@router.post("/{camera_id}/process-frame", response_model=CameraFrameResponse)
def process_frame(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
    _attendance_access=Depends(require_module("attendance")),
) -> CameraFrameResponse:
    return _run_frame_action(
        db,
        current_admin.tenant_id,
        camera_id,
        recognize=False,
    )


@router.post("/{camera_id}/recognize-frame", response_model=CameraFrameResponse)
def recognize_frame(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
    _attendance_access=Depends(require_module("attendance")),
) -> CameraFrameResponse:
    return _run_frame_action(
        db,
        current_admin.tenant_id,
        camera_id,
        recognize=True,
    )


@router.post("/{camera_id}/recognize-and-mark-attendance", response_model=CameraFrameResponse)
def recognize_and_mark_camera_attendance(
    camera_id: str,
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
    _attendance_access=Depends(require_module("attendance")),
) -> CameraFrameResponse:
    return _run_frame_action(
        db,
        current_admin.tenant_id,
        camera_id,
        recognize=True,
        mark=True,
    )

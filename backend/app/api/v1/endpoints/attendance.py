"""Authenticated attendance recognition routes."""

from __future__ import annotations

import base64
import binascii
import logging
from time import perf_counter
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import TypeAdapter, ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import database_session, get_current_tenant_admin, get_current_tenant_user, require_module
from app.schemas.attendance import (
    AttendanceEventRead,
    AttendanceMarkRequest,
    AttendanceMarkResponse,
    DailyAttendanceRead,
    RecognizeAndMarkResponse,
    TodayAttendanceItem,
    TodayAttendanceResponse,
)
from app.schemas.recognition import RecognitionBase64Request, RecognitionMode, RecognitionResponse
from app.services.audit_service import log_recognition_attempt
from app.services.attendance_service import (
    AttendanceMarkError,
    list_today_attendance,
    log_live_recognition_decision,
    mark_attendance,
    process_camera_presence_recognition,
)
from app.services.face_ai_service import FaceModelUnavailableError, FaceValidationError
from app.services.recognition_service import recognize_employee_face
from app.services.camera_service import get_camera

router = APIRouter(dependencies=[Depends(require_module("attendance"))])
mode_adapter = TypeAdapter(RecognitionMode)
logger = logging.getLogger(__name__)


def _decode_base64_frame(frame: str) -> bytes:
    encoded = frame.split(",", 1)[1] if frame.startswith("data:") and "," in frame else frame
    try:
        content = base64.b64decode("".join(encoded.split()), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_IMAGE", "message": "The base64 frame is invalid."},
        ) from exc
    return content


def _validate_image_size(content: bytes) -> bytes:
    max_bytes = settings.upload_max_image_mb * 1024 * 1024
    if not content:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "INVALID_IMAGE", "message": "The image is empty."},
        )
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "code": "INVALID_IMAGE",
                "message": f"The image exceeds the {settings.upload_max_image_mb} MB upload limit.",
            },
        )
    return content


async def _recognition_input(request: Request) -> tuple[bytes, str | None, RecognitionMode]:
    content_type = request.headers.get("content-type", "").lower()
    if content_type.startswith("multipart/form-data"):
        form = await request.form()
        upload = form.get("image") or form.get("file")
        if upload is None or not hasattr(upload, "read"):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_IMAGE", "message": "An image file is required."},
            )
        image_content = await upload.read()
        camera_id = str(form["camera_id"]) if form.get("camera_id") else None
        try:
            mode = mode_adapter.validate_python(form.get("mode") or "attendance")
        except ValidationError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="mode must be attendance, access, or visitor",
            ) from exc
        return _validate_image_size(image_content), camera_id, mode

    if content_type.startswith("application/json"):
        try:
            payload = RecognitionBase64Request.model_validate(await request.json())
        except (ValidationError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"code": "INVALID_IMAGE", "message": "A valid base64 image frame is required."},
            ) from exc
        return _validate_image_size(_decode_base64_frame(payload.frame)), payload.camera_id, payload.mode

    raise HTTPException(
        status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
        detail="Use multipart/form-data or application/json.",
    )


def _failed_audit_result(recognition_status: str) -> dict:
    return {
        "recognized": False,
        "employee_id": None,
        "confidence": None,
        "distance": None,
        "threshold": settings.face_recognition_threshold,
        "recognition_status": recognition_status,
    }


def _camera_presence_state(db: Session, tenant_id: str, camera_id: str | None) -> tuple[bool, str | None, str | None]:
    if not camera_id:
        return True, None, None
    camera = get_camera(db, tenant_id, camera_id)
    if camera is None:
        return False, None, None
    return bool(camera.is_active), camera.id, camera.name


def _attendance_response(result: dict) -> AttendanceMarkResponse:
    return AttendanceMarkResponse(
        event=AttendanceEventRead.model_validate(result["event"]),
        daily=DailyAttendanceRead.model_validate(result["daily"]),
        employee_id=str(result["employee"].id),
        employee_name=result["employee"].full_name,
        employee_code=result["employee"].employee_code,
        message=result["message"],
    )


def _raise_mark_error(exc: AttendanceMarkError) -> None:
    raise HTTPException(
        status_code=exc.status_code,
        detail={"code": exc.code, "message": exc.message},
    ) from exc


def _ensure_own_employee(current_user, employee_id: str) -> None:
    if getattr(current_user, "role", None) != "user":
        return
    try:
        linked_id_is_valid = bool(current_user.employee_id and UUID(current_user.employee_id))
    except ValueError:
        linked_id_is_valid = False
    if not linked_id_is_valid or current_user.employee_id != employee_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant users may only access their own attendance",
        )


@router.post("/check-in", response_model=AttendanceMarkResponse, status_code=status.HTTP_201_CREATED)
def check_in(
    payload: AttendanceMarkRequest,
    db: Session = Depends(database_session),
    current_user=Depends(get_current_tenant_user),
) -> AttendanceMarkResponse:
    _ensure_own_employee(current_user, payload.employee_id)
    try:
        result = mark_attendance(
            db,
            current_user.tenant_id,
            payload.employee_id,
            event_type="check_in",
            source=payload.source,
            camera_id=payload.camera_id,
            confidence=payload.confidence,
            event_time=payload.event_time,
            metadata=payload.metadata,
        )
    except AttendanceMarkError as exc:
        _raise_mark_error(exc)
    return _attendance_response(result)


@router.post("/check-out", response_model=AttendanceMarkResponse, status_code=status.HTTP_201_CREATED)
def check_out(
    payload: AttendanceMarkRequest,
    db: Session = Depends(database_session),
    current_user=Depends(get_current_tenant_user),
) -> AttendanceMarkResponse:
    _ensure_own_employee(current_user, payload.employee_id)
    try:
        result = mark_attendance(
            db,
            current_user.tenant_id,
            payload.employee_id,
            event_type="check_out",
            source=payload.source,
            camera_id=payload.camera_id,
            confidence=payload.confidence,
            event_time=payload.event_time,
            metadata=payload.metadata,
        )
    except AttendanceMarkError as exc:
        _raise_mark_error(exc)
    return _attendance_response(result)


@router.get("/today", response_model=TodayAttendanceResponse)
def today_attendance(
    db: Session = Depends(database_session),
    current_user=Depends(get_current_tenant_user),
) -> TodayAttendanceResponse:
    employee_id = current_user.employee_id if getattr(current_user, "role", None) == "user" else None
    try:
        linked_id_is_valid = bool(employee_id and UUID(employee_id))
    except ValueError:
        linked_id_is_valid = False
    if getattr(current_user, "role", None) == "user" and not linked_id_is_valid:
        return TodayAttendanceResponse(records=[])
    rows = list_today_attendance(db, current_user.tenant_id, employee_id=employee_id)
    return TodayAttendanceResponse(
        records=[
            TodayAttendanceItem(
                **DailyAttendanceRead.model_validate(row["record"]).model_dump(),
                employee_name=row["employee_name"],
                employee_code=row["employee_code"],
            )
            for row in rows
        ]
    )


@router.post(
    "/recognize",
    response_model=RecognitionResponse,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "multipart/form-data": {
                    "schema": {
                        "type": "object",
                        "required": ["image"],
                        "properties": {
                            "image": {"type": "string", "format": "binary"},
                            "camera_id": {"type": "string", "nullable": True},
                            "mode": {
                                "type": "string",
                                "enum": ["attendance", "access", "visitor"],
                                "default": "attendance",
                            },
                        },
                    }
                },
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "image": {
                                "type": "string",
                                "description": "Raw base64 or a data URL.",
                            },
                            "base64_frame": {"type": "string"},
                            "camera_id": {"type": "string", "nullable": True},
                            "mode": {
                                "type": "string",
                                "enum": ["attendance", "access", "visitor"],
                                "default": "attendance",
                            },
                        },
                    }
                },
            },
        }
    },
)
async def recognize_attendance_face(
    request: Request,
    db: Session = Depends(database_session),
    current_user=Depends(get_current_tenant_admin),
) -> RecognitionResponse:
    camera_id: str | None = None
    mode: RecognitionMode = "attendance"
    try:
        started_at = perf_counter()
        image_content, camera_id, mode = await _recognition_input(request)
        result = recognize_employee_face(db, current_user.tenant_id, image_content)
    except HTTPException:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result("INVALID_IMAGE"),
            camera_id=camera_id,
            mode=mode,
        )
        raise
    except FaceValidationError as exc:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result(exc.code),
            camera_id=camera_id,
            mode=mode,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    except FaceModelUnavailableError as exc:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result("MODEL_UNAVAILABLE"),
            camera_id=camera_id,
            mode=mode,
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    log_recognition_attempt(
        db,
        tenant_id=current_user.tenant_id,
        tenant_member_id=current_user.id,
        result=result,
        camera_id=camera_id,
        mode=mode,
    )
    processing_ms = int((perf_counter() - started_at) * 1000)
    recognition_response = RecognitionResponse.model_validate(result)
    if recognition_response.recognized:
        log_live_recognition_decision(
            camera_enabled=bool(camera_id),
            tenant_id=current_user.tenant_id,
            camera_id=camera_id,
            frame_received=True,
            face_detected=True,
            matched=True,
            faces_detected=int(result.get("face_count") or 1),
            employee_id=recognition_response.employee_id,
            employee_name=recognition_response.employee_name,
            confidence=recognition_response.confidence,
            processing_ms=processing_ms,
            decided_event="recognized",
            final_status="recognized",
            reason="Person detected successfully",
        )
        return recognition_response

    log_live_recognition_decision(
        camera_enabled=bool(camera_id),
        tenant_id=current_user.tenant_id,
        camera_id=camera_id,
        frame_received=True,
        face_detected=recognition_response.recognition_status != "NO_FACE",
        matched=False,
        faces_detected=int(result.get("face_count") or 0),
        employee_id=None,
        employee_name=None,
        confidence=recognition_response.confidence,
        processing_ms=processing_ms,
        decided_event=(
            "no_face"
            if recognition_response.recognition_status == "NO_FACE"
            else "unknown_face"
            if recognition_response.recognition_status == "UNKNOWN"
            else "error"
        ),
        final_status="not_detected",
        reason=(
            "No face detected"
            if recognition_response.recognition_status == "NO_FACE"
            else "Unknown face detected"
            if recognition_response.recognition_status == "UNKNOWN"
            else "Face did not match"
        ),
    )
    return recognition_response


@router.post("/recognize-and-mark", response_model=RecognizeAndMarkResponse)
async def recognize_and_mark_attendance(
    request: Request,
    db: Session = Depends(database_session),
    current_user=Depends(get_current_tenant_admin),
) -> RecognizeAndMarkResponse:
    camera_id: str | None = None
    mode: RecognitionMode = "attendance"
    try:
        started_at = perf_counter()
        image_content, camera_id, mode = await _recognition_input(request)
        camera_enabled, resolved_camera_id, _camera_name = _camera_presence_state(db, current_user.tenant_id, camera_id)
        recognition = recognize_employee_face(db, current_user.tenant_id, image_content)
    except HTTPException:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result("INVALID_IMAGE"),
            camera_id=camera_id,
            mode=mode,
        )
        raise
    except FaceValidationError as exc:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result(exc.code),
            camera_id=camera_id,
            mode=mode,
        )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": exc.code, "message": exc.message},
        ) from exc
    except FaceModelUnavailableError as exc:
        log_recognition_attempt(
            db,
            tenant_id=current_user.tenant_id,
            tenant_member_id=current_user.id,
            result=_failed_audit_result("MODEL_UNAVAILABLE"),
            camera_id=camera_id,
            mode=mode,
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    log_recognition_attempt(
        db,
        tenant_id=current_user.tenant_id,
        tenant_member_id=current_user.id,
        result=recognition,
        camera_id=camera_id,
        mode=mode,
    )
    recognition_response = RecognitionResponse.model_validate(recognition)
    if not recognition["recognized"]:
        log_live_recognition_decision(
            camera_enabled=camera_enabled,
            tenant_id=current_user.tenant_id,
            camera_id=resolved_camera_id or camera_id,
            frame_received=True,
            face_detected=recognition["recognition_status"] != "NO_FACE",
            matched=False,
            employee_id=None,
            employee_name=None,
            confidence=recognition.get("confidence"),
            decided_event=(
                "no_face"
                if recognition["recognition_status"] == "NO_FACE"
                else "unknown_face"
                if recognition["recognition_status"] == "UNKNOWN"
                else "error"
            ),
            final_status="absent",
            reason=(
                "No face detected"
                if recognition["recognition_status"] == "NO_FACE"
                else "Unknown face detected"
                if recognition["recognition_status"] == "UNKNOWN"
                else "Face did not match"
            ),
        )
        return RecognizeAndMarkResponse(recognition=recognition_response, attendance=None)

    try:
        presence = process_camera_presence_recognition(
            db,
            current_user.tenant_id,
            employee_id=recognition["employee_id"],
            employee_name=recognition.get("employee_name"),
            confidence=recognition["confidence"],
            recognition_status=recognition["recognition_status"],
            camera_id=resolved_camera_id or camera_id,
            camera_enabled=camera_enabled,
            faces_detected=int(recognition.get("face_count") or 1),
            processing_ms=int((perf_counter() - started_at) * 1000),
        )
    except AttendanceMarkError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
                "recognition": recognition,
            },
        ) from exc
    return RecognizeAndMarkResponse(
        recognition=recognition_response,
        attendance=_attendance_response(presence["attendance"]) if presence["attendance"] is not None else None,
    )

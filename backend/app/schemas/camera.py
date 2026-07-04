"""Camera management schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.attendance import AttendanceMarkResponse
from app.schemas.recognition import RecognitionResponse

CameraType = Literal[
    "ip_webcam", "phone_ip_webcam", "rtsp", "http_mjpeg",
    "webcam", "manual", "manual_snapshot",
]
CameraFeatureScope = Literal["attendance", "object_detection", "both"]
CameraHealth = Literal["online", "offline", "error", "unknown"]


def _validate_url(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    parsed = urlparse(normalized)
    if parsed.scheme.lower() not in {"http", "https", "rtsp", "rtsps"} or not parsed.netloc:
        raise ValueError("Camera URLs must use http, https, rtsp, or rtsps")
    return normalized


class CameraDetectionZone(BaseModel):
    id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=100)
    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(gt=0, le=100)
    height: float = Field(gt=0, le=100)


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    camera_type: CameraType
    phone_ip: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    stream_url: str | None = None
    snapshot_url: str | None = None
    assigned_feature_scope: CameraFeatureScope = "both"
    detection_zones: list[CameraDetectionZone] = Field(default_factory=list)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=500)
    is_active: bool = True

    _stream_url = field_validator("stream_url")(_validate_url)
    _snapshot_url = field_validator("snapshot_url")(_validate_url)


class CameraUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    location: str | None = Field(default=None, min_length=1, max_length=255)
    camera_type: CameraType | None = None
    phone_ip: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    stream_url: str | None = None
    snapshot_url: str | None = None
    assigned_feature_scope: CameraFeatureScope | None = None
    detection_zones: list[CameraDetectionZone] | None = None
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=500)
    clear_password: bool = False
    is_active: bool | None = None

    _stream_url = field_validator("stream_url")(_validate_url)
    _snapshot_url = field_validator("snapshot_url")(_validate_url)


class CameraRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    location: str
    camera_type: CameraType
    phone_ip: str | None = None
    port: int | None = None
    stream_url: str | None = None
    snapshot_url: str | None = None
    assigned_feature_scope: CameraFeatureScope = "both"
    detection_zones: list[CameraDetectionZone] = Field(default_factory=list)
    username: str | None = None
    has_credentials: bool = False
    is_active: bool
    health_status: CameraHealth
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraListResponse(BaseModel):
    cameras: list[CameraRead] = Field(default_factory=list)


class CameraTestResponse(BaseModel):
    camera_id: str
    success: bool
    health_status: CameraHealth
    message: str
    width: int | None = None
    height: int | None = None
    content_type: str | None = None


class CameraEventRead(BaseModel):
    id: str
    tenant_id: str
    camera_id: str
    event_type: str
    employee_id: str | None = None
    recognition_status: str
    confidence: float | None = None
    image_path: str | None = None
    metadata: dict = Field(validation_alias="event_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CameraFrameMetadata(BaseModel):
    width: int
    height: int
    content_type: str
    frame_interval_seconds: int
    request_timeout_seconds: int


class CameraFrameResponse(BaseModel):
    camera: CameraRead
    camera_event: CameraEventRead
    frame: CameraFrameMetadata
    recognition: RecognitionResponse | None = None
    attendance: AttendanceMarkResponse | None = None

"""Person detection schemas."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.employee import EmployeeFaceProfileRead, EmployeeRead
from app.schemas.visitor import VisitorRead, VisitorVisitRead

PersonDetectionMatchType = Literal["staff", "visitor", "unknown"]
PersonDetectionStatus = Literal["new", "reviewed", "suspicious", "converted_to_visitor", "converted_to_staff", "ignored"]


class PersonDetectionRead(BaseModel):
    id: str
    tenant_id: str
    camera_id: str
    zone_id: str | None = None
    image_path: str | None = None
    detected_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime
    seen_count: int
    snapshot_quality_score: float | None = None
    face_embedding: list[float] | None = None
    match_type: PersonDetectionMatchType
    matched_staff_id: str | None = None
    matched_visitor_id: str | None = None
    status: PersonDetectionStatus
    note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PersonDetectionListResponse(BaseModel):
    detections: list[PersonDetectionRead] = Field(default_factory=list)


class PersonDetectionDetailResponse(PersonDetectionRead):
    pass


class PersonDetectionNoteRequest(BaseModel):
    note: str = Field(min_length=1)


class PersonDetectionAddVisitorRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    purpose: str | None = None
    status: Literal["active", "important", "blocked"] = "active"
    notes: str | None = None
    visitor_id: str | None = None


class PersonDetectionAddVisitorResponse(BaseModel):
    visitor: VisitorRead
    visit: VisitorVisitRead
    person_detection: PersonDetectionDetailResponse


class PersonDetectionAddStaffRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    employee_code: str | None = Field(default=None, max_length=100)
    department: str | None = Field(default=None, max_length=100)
    designation: str | None = Field(default=None, max_length=100)
    mobile: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    joining_date: date | None = None
    status: Literal["active", "inactive"] = "active"


class PersonDetectionAddStaffResponse(BaseModel):
    employee: EmployeeRead
    person_detection: PersonDetectionDetailResponse
    face_profile: EmployeeFaceProfileRead

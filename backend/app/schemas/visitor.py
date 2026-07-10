"""Visitor registration and visit history schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VisitorStatus = Literal["active", "important", "blocked", "expected", "checked_in", "checked_out"]


class VisitorCreate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    purpose: str | None = Field(default=None)
    photo_url: str | None = None
    image_path: str | None = None
    face_embedding: list[float] | None = None
    status: VisitorStatus = "active"
    notes: str | None = None


class VisitorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    purpose: str | None = Field(default=None)
    photo_url: str | None = None
    image_path: str | None = None
    face_embedding: list[float] | None = None
    status: VisitorStatus | None = None
    notes: str | None = None


class VisitorRead(BaseModel):
    id: str
    tenant_id: str
    name: str
    full_name: str
    phone: str | None = None
    email: str | None = None
    company: str | None = None
    purpose: str | None = None
    photo_url: str | None = None
    image_path: str | None = None
    face_embedding: list[float] | None = None
    first_seen_at: datetime | None = None
    last_seen_at: datetime | None = None
    total_visits: int
    status: VisitorStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VisitorVisitRead(BaseModel):
    id: str
    tenant_id: str
    visitor_id: str
    person_detection_id: str | None = None
    camera_id: str | None = None
    zone_id: str | None = None
    seen_at: datetime
    snapshot_url: str | None = None
    image_path: str | None = None
    check_in_time: datetime
    check_out_time: datetime | None = None
    access_status: str
    notes: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VisitorDetail(VisitorRead):
    visits: list[VisitorVisitRead] = Field(default_factory=list)


class VisitorListResponse(BaseModel):
    visitors: list[VisitorRead] = Field(default_factory=list)


class VisitorVisitListResponse(BaseModel):
    visits: list[VisitorVisitRead] = Field(default_factory=list)


class VisitorCheckIn(BaseModel):
    access_status: str = Field(default="granted", min_length=1, max_length=50)
    notes: str | None = None


class VisitorCheckOut(BaseModel):
    notes: str | None = None


class VisitorNoteRequest(BaseModel):
    note: str = Field(min_length=1)


class VisitorVisitActionResponse(BaseModel):
    visitor: VisitorRead
    visit: VisitorVisitRead

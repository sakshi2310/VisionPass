"""Visitor registration and visit history schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VisitorStatus = Literal["expected", "checked_in", "checked_out", "blocked"]


class VisitorCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    purpose: str = Field(min_length=1)
    host_employee_id: str | None = None
    photo_path: str | None = None
    status: VisitorStatus = "expected"


class VisitorUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone: str | None = Field(default=None, min_length=1, max_length=50)
    email: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    purpose: str | None = Field(default=None, min_length=1)
    host_employee_id: str | None = None
    photo_path: str | None = None
    status: VisitorStatus | None = None


class VisitorRead(BaseModel):
    id: str
    tenant_id: str
    full_name: str
    phone: str
    email: str | None = None
    company: str | None = None
    purpose: str
    host_employee_id: str | None = None
    photo_path: str | None = None
    status: VisitorStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VisitorVisitRead(BaseModel):
    id: str
    tenant_id: str
    visitor_id: str
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


class VisitorCheckIn(BaseModel):
    access_status: str = Field(default="granted", min_length=1, max_length=50)
    notes: str | None = None


class VisitorCheckOut(BaseModel):
    notes: str | None = None


class VisitorVisitActionResponse(BaseModel):
    visitor: VisitorRead
    visit: VisitorVisitRead

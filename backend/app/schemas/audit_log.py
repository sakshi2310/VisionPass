"""Audit log schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AdminAuditLogRead(BaseModel):
    id: str
    user: str
    action: str
    entity: str
    entity_id: str | None = None
    note: str | None = None
    details: dict | None = None
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminAuditLogListResponse(BaseModel):
    logs: list[AdminAuditLogRead] = Field(default_factory=list)

"""Alert lifecycle schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

AlertSeverity = Literal["low", "medium", "high", "critical"]
AlertStatus = Literal["open", "acknowledged", "resolved"]


class AlertRead(BaseModel):
    id: str
    tenant_id: str
    alert_type: str
    severity: AlertSeverity
    title: str
    message: str
    status: AlertStatus
    source_type: str
    source_id: str | None = None
    metadata: dict = Field(validation_alias="alert_metadata")
    created_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    alerts: list[AlertRead] = Field(default_factory=list)

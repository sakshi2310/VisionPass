"""Access decision request and log schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

AccessDecision = Literal["granted", "denied", "manual_review"]
RecognitionStatus = Literal["MATCHED", "UNKNOWN", "LOW_CONFIDENCE", "NO_FACE", "MULTIPLE_FACES"]


class AccessDecisionRequest(BaseModel):
    tenant_id: str
    employee_id: str | None = None
    visitor_id: str | None = None
    camera_id: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    recognition_status: RecognitionStatus
    timestamp: datetime

    @model_validator(mode="after")
    def one_identity_at_most(self):
        if self.employee_id and self.visitor_id:
            raise ValueError("employee_id and visitor_id cannot both be provided")
        return self


class AccessLogRead(BaseModel):
    id: str
    tenant_id: str
    employee_id: str | None = None
    visitor_id: str | None = None
    camera_id: str | None = None
    decision: AccessDecision
    reason: str
    confidence: float | None = None
    created_at: datetime
    identity_name: str | None = None
    camera_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AccessDecisionResponse(BaseModel):
    decision: AccessDecision
    reason: str
    log: AccessLogRead


class AccessLogListResponse(BaseModel):
    logs: list[AccessLogRead] = Field(default_factory=list)

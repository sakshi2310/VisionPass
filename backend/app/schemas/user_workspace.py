"""Schemas for the tenant user workspace."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserWorkspaceFeature(BaseModel):
    feature_name: str
    feature_code: str
    description: str | None = None
    module_key: str | None = None
    route: str | None = None


class UserWorkspaceProfile(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    status: str
    tenant_id: str
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    employee_id: str | None = None
    last_login_at: datetime | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserWorkspaceSummary(BaseModel):
    tenant_name: str
    member_name: str
    member_role: str
    tenant_id: str
    member_id: str
    profile_status: str
    assigned_features_count: int = 0
    open_modules_count: int = 0


class UserWorkspaceDashboardResponse(BaseModel):
    summary: UserWorkspaceSummary
    profile: UserWorkspaceProfile | None = None
    features: list[UserWorkspaceFeature] = Field(default_factory=list)

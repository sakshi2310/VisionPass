"""Tenant admin dashboards and member schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, AliasChoices


class TenantAdminMemberRead(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    status: str
    is_active: bool
    assigned_features: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantAdminMemberListResponse(BaseModel):
    members: list[TenantAdminMemberRead] = Field(default_factory=list)


class TenantAdminMemberCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "user"
    status: str = "active"
    assigned_features: list[str] = Field(default_factory=list, validation_alias=AliasChoices("assigned_features", "feature_codes"))


class TenantAdminMemberUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None
    status: str | None = None
    assigned_features: list[str] | None = Field(default=None, validation_alias=AliasChoices("assigned_features", "feature_codes"))


class TenantAdminDashboardSummary(BaseModel):
    total_members: int = 0
    tenant_admins: int = 0
    users: int = 0
    enabled_features: int = 0


class TenantAdminFeatureRead(BaseModel):
    feature_name: str
    feature_code: str
    description: str | None = None


class TenantAdminFeatureListResponse(BaseModel):
    features: list[TenantAdminFeatureRead] = Field(default_factory=list)


class TenantAdminMemberFeaturesUpdate(BaseModel):
    assigned_features: list[str] = Field(default_factory=list, validation_alias=AliasChoices("assigned_features", "feature_codes"))


class TenantAdminMemberFeatureCodesResponse(BaseModel):
    assigned_features: list[str] = Field(default_factory=list)

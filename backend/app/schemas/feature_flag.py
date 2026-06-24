"""Feature flag schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeatureFlagRead(BaseModel):
    id: str | None = None
    tenant_id: str
    module_name: str
    enabled: bool
    config: dict | None = None
    updated_by: str | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeatureFlagToggleRequest(BaseModel):
    enabled: bool
    config: dict | None = None


class TenantModulesResponse(BaseModel):
    tenant_id: str
    modules: list[FeatureFlagRead]


class EnabledModulesResponse(BaseModel):
    tenant_id: str | None
    enabled_modules: list[str]

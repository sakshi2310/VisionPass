"""Admin management schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.cv_feature import CvFeatureRead
from app.schemas.user import UserRead


class AdminTenantRead(BaseModel):
    id: str
    name: str
    slug: str
    code: str
    plan: str
    status: str
    industry: str = "General"
    logo_url: str | None = None
    address: str | None = None
    admin_name: str | None = None
    admin_email: str | None = None
    phone: str | None = None
    max_users: int = 100
    max_devices: int = 20
    features_count: int = 0
    enabled_modules: list[str] = Field(default_factory=list)
    users: int = 0
    sites: int = 1
    alerts_today: int = 0
    cameras: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminTenantCreate(BaseModel):
    full_name: str
    email: str
    phone: str | None = None
    password: str
    organization_name: str
    slug: str | None = None
    logo_url: str | None = None
    address: str | None = None
    status: str = "active"
    industry: str = "General"
    max_users: int = 100
    max_devices: int = 20
    enabled_modules: list[str] = Field(default_factory=list)


class AdminTenantUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    logo_url: str | None = None
    address: str | None = None
    status: str | None = None
    industry: str | None = None
    admin_name: str | None = None
    admin_email: str | None = None
    phone: str | None = None
    max_users: int | None = None
    max_devices: int | None = None
    enabled_modules: list[str] | None = None


class AdminDashboardSummaryRead(BaseModel):
    total_tenants: int = 0
    active_tenants: int = 0
    total_tenant_admins: int = 0
    total_users: int = 0
    total_features: int = 0
    active_sessions: int = 0


class AdminTenantDetailsRead(BaseModel):
    tenant: AdminTenantRead
    admins: list[UserRead] = Field(default_factory=list)
    users: list[UserRead] = Field(default_factory=list)
    assigned_features: list[CvFeatureRead] = Field(default_factory=list)
    activity_summary: dict[str, int] = Field(default_factory=dict)


class TenantModulesUpdate(BaseModel):
    enabled_modules: list[str] = Field(default_factory=list)

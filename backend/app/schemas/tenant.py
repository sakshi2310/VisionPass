"""Tenant schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TenantBase(BaseModel):
    name: str
    slug: str
    company_email: str | None = None
    logo_url: str | None = None
    address: str | None = None
    industry: str = "General"
    status: str = "active"
    plan: str = "basic"


class TenantRead(TenantBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

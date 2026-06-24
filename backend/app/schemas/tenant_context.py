"""Tenant context schemas."""

from pydantic import BaseModel


class TenantContext(BaseModel):
    tenant_id: str | None
    user_role: str
    is_super_admin: bool

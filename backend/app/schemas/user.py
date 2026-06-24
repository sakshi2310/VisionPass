"""User schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    email: str
    full_name: str
    role: str = "user"
    tenant_id: str | None = None
    phone: str | None = None
    department: str | None = None
    designation: str | None = None
    employee_id: str | None = None
    access_zones: list[str] = Field(default_factory=list)
    face_enrolled: bool = False
    is_active: bool = True
    is_deleted: bool = False
    notes: str | None = None
    last_login_at: datetime | None = None
    created_by: str | None = None


class UserRead(UserBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TenantUserRead(UserRead):
    model_config = ConfigDict(from_attributes=True)


class TenantUserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    phone: str | None = None
    role: str = "user"
    department: str | None = None
    designation: str | None = None
    employee_id: str | None = None
    access_zones: list[str] = Field(default_factory=list)
    is_active: bool = True
    face_enrolled: bool = False
    notes: str | None = None


class TenantUserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    password: str | None = None
    phone: str | None = None
    role: str | None = None
    department: str | None = None
    designation: str | None = None
    employee_id: str | None = None
    access_zones: list[str] | None = None
    is_active: bool | None = None
    face_enrolled: bool | None = None
    notes: str | None = None


class TenantUserListResponse(BaseModel):
    users: list[TenantUserRead]

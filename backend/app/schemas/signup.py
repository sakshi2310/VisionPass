"""Signup response schemas."""

from pydantic import BaseModel

from app.schemas.tenant import TenantRead
from app.schemas.user import UserRead


class SignupResponse(BaseModel):
    tenant: TenantRead
    user: UserRead


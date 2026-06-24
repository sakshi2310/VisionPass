"""Auth schemas."""

from pydantic import BaseModel

from app.schemas.tenant import TenantRead
from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    full_name: str
    email: str
    organization_name: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class BootstrapRequest(BaseModel):
    full_name: str
    email: str
    password: str
    organization_name: str = "VisionPass Platform"


class BootstrapStatusResponse(BaseModel):
    setup_required: bool


class AuthResponse(BaseModel):
    token: TokenResponse
    user: UserRead
    tenant: TenantRead | None = None

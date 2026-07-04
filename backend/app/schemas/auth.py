"""Auth schemas."""

from pydantic import BaseModel, Field, computed_field

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
    features: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def access_token(self) -> str:
        """Top-level token field for common auth clients; nested token stays compatible."""
        return self.token.access_token

    @computed_field
    @property
    def token_type(self) -> str:
        return self.token.token_type

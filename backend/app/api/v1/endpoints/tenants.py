"""Tenant routes."""

from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.schemas.tenant_context import TenantContext
from app.schemas.tenant import TenantRead
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=TenantContext)
def get_current_tenant_context(current_user=Depends(get_current_user)) -> TenantContext:
    return TenantContext(
        tenant_id=getattr(current_user, "tenant_id", None),
        user_role=getattr(current_user, "role", "user"),
        is_super_admin=getattr(current_user, "role", "") == "super_admin",
    )

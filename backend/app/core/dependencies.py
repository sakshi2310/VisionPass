"""FastAPI dependencies."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.feature_flag import FeatureFlag
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember
from app.services.feature_flag_service import ensure_module_access

bearer_scheme = HTTPBearer(auto_error=False)

TENANT_USER_ROLES = {
    "tenant_admin",
    "client_admin",
    "user",
}
TENANT_ADMIN_ROLES = {
    "tenant_admin",
    "client_admin",
}


def _normalize_role(value: str | None) -> str:
    return (value or "").strip().lower()


def database_session(db: Session = Depends(get_db)) -> Session:
    return db


def _load_active_tenant(db: Session, tenant_id: str | None) -> Tenant | None:
    if tenant_id is None:
        return None
    return (
        db.query(Tenant)
        .filter(
            Tenant.id == tenant_id,
            Tenant.is_deleted.is_(False),
            Tenant.status == "active",
        )
        .one_or_none()
    )


def _ensure_user_tenant_accessible(db: Session, user: TenantMember | SuperAdmin) -> None:
    if _normalize_role(getattr(user, "role", None)) == "super_admin":
        return

    tenant = _load_active_tenant(db, getattr(user, "tenant_id", None))
    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant suspended or inactive",
        )


def _load_current_account(db: Session, subject: str, role: str | None, principal_type: str | None):
    normalized_type = _normalize_role(role or principal_type)
    if normalized_type == "super_admin":
        return db.query(SuperAdmin).filter(SuperAdmin.id == subject).one_or_none()
    return db.query(TenantMember).filter(TenantMember.id == subject).one_or_none()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
):
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub") or payload.get("id")
        principal_type = payload.get("principal_type")
        role = payload.get("role")
    except Exception as exc:  # pragma: no cover - defensive auth guard
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
        )

    user = _load_current_account(db, subject, role, principal_type)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    if _normalize_role(getattr(user, "role", None)) == "super_admin":
        if getattr(user, "status", None) != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
    else:
        if not user.is_active or user.is_deleted or user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )
        _ensure_user_tenant_accessible(db, user)

    return user


def get_current_tenant_admin(current_user = Depends(get_current_user)):
    if _normalize_role(getattr(current_user, "role", None)) not in TENANT_ADMIN_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant admin access required",
        )
    return current_user


def get_current_tenant_user(current_user = Depends(get_current_user)):
    if _normalize_role(getattr(current_user, "role", None)) not in TENANT_USER_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant user access required",
        )
    return current_user


def require_module(module_name: str) -> Callable:
    def dependency(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
        if _normalize_role(getattr(current_user, "role", None)) == "super_admin":
            return current_user

        if not ensure_module_access(db, current_user, module_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Module access denied: {module_name}",
            )

        return current_user

    return dependency


def require_role(allowed_roles: list[str]) -> Callable:
    normalized_allowed = {_normalize_role(role) for role in allowed_roles}

    def dependency(current_user = Depends(get_current_user)):
        if _normalize_role(getattr(current_user, "role", None)) not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return dependency

"""Auth service."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_member import TenantMember

logger = get_logger("auth")
TENANT_USER_ROLES = {
    "tenant_admin",
    "user",
}


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "visionpass-platform"


def normalize_role(role: str | None) -> str:
    return (role or "").strip().lower()


def build_display_role(role: str) -> str:
    normalized = normalize_role(role)
    mapping = {
        "super_admin": "Platform Super Admin",
        "tenant_admin": "Tenant Admin",
        "user": "Tenant User",
    }
    return mapping.get(normalized, "Vision Pass")


def has_super_admin(db: Session) -> bool:
    return db.query(SuperAdmin.id).limit(1).one_or_none() is not None


def _ensure_tenant_active(db: Session, tenant_id: str | None) -> Tenant:
    tenant = (
        db.query(Tenant)
        .filter(
            Tenant.id == tenant_id,
            Tenant.is_deleted.is_(False),
            Tenant.status == "active",
        )
        .one_or_none()
    )
    if tenant is None:
        raise ValueError("Tenant suspended")
    return tenant


def _touch_login(account: Any, db: Session) -> None:
    account.last_login_at = datetime.now(timezone.utc)
    db.add(account)
    db.commit()
    db.refresh(account)


def issue_login_token(account: Any) -> str:
    role = normalize_role(getattr(account, "role", None))
    claims: dict[str, Any] = {
        "id": str(account.id),
        "email": account.email,
        "role": role,
    }
    if role == "super_admin":
        claims["principal_type"] = "super_admin"
    else:
        claims["principal_type"] = "tenant_member"
        claims["tenant_id"] = getattr(account, "tenant_id", None)

    return create_access_token(
        subject=str(account.id),
        expires_delta=timedelta(hours=8),
        additional_claims=claims,
    )


def _verify_active_member(user: TenantMember) -> None:
    if user.status != "active" or not user.is_active or user.is_deleted:
        raise ValueError("Account inactive")


def _find_super_admin_by_email(db: Session, email: str) -> SuperAdmin | None:
    normalized_email = email.lower().strip()
    return db.query(SuperAdmin).filter(SuperAdmin.email == normalized_email).one_or_none()


def _find_tenant_member_and_tenant_by_email(db: Session, email: str) -> tuple[TenantMember, Tenant] | None:
    normalized_email = email.lower().strip()
    row = (
        db.query(TenantMember, Tenant)
        .join(Tenant, Tenant.id == TenantMember.tenant_id)
        .filter(TenantMember.email == normalized_email)
        .one_or_none()
    )
    if row is None:
        return None
    member, tenant = row
    return member, tenant


def authenticate_super_admin_login(db: Session, email: str, password: str) -> SuperAdmin:
    admin = _find_super_admin_by_email(db, email)
    if admin is None:
        raise ValueError("Invalid credentials")
    if admin.status != "active":
        raise ValueError("Account inactive")
    if not verify_password(password, admin.password_hash):
        raise ValueError("Invalid credentials")
    _touch_login(admin, db)
    return admin


def authenticate_login(db: Session, email: str, password: str) -> tuple[Tenant, TenantMember]:
    return authenticate_tenant_member_login(db, email, password)


def authenticate_tenant_admin_login(db: Session, email: str, password: str) -> tuple[Tenant, TenantMember]:
    return authenticate_tenant_member_login(db, email, password, required_role="tenant_admin")


def authenticate_tenant_member_login(
    db: Session,
    email: str,
    password: str,
    required_role: str | None = None,
) -> tuple[Tenant, TenantMember]:
    row = _find_tenant_member_and_tenant_by_email(db, email)
    if row is None:
        raise ValueError("Invalid credentials")

    user, tenant = row
    normalized_role = normalize_role(user.role)
    if required_role is not None and normalized_role != normalize_role(required_role):
        raise ValueError("Invalid credentials")
    if normalized_role not in TENANT_USER_ROLES:
        raise ValueError("Invalid credentials")

    _verify_active_member(user)
    _ensure_tenant_active(db, tenant.id)
    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid credentials")

    _touch_login(user, db)
    return tenant, user


def authenticate_tenant_user_login(db: Session, email: str, password: str) -> tuple[Tenant, TenantMember]:
    return authenticate_tenant_member_login(db, email, password, required_role="user")


def create_first_super_admin(
    db: Session,
    full_name: str,
    email: str,
    organization_name: str,
    password: str,
) -> tuple[Tenant | None, SuperAdmin]:
    logger.info(f'>>> CREATE SUPER ADMIN REQUEST -- Org: "{organization_name.strip() or "VisionPass Platform"}"')
    admin = SuperAdmin(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        status="active",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    logger.info(f'OK SUPER ADMIN CREATED -- Admin: "{admin.full_name}" (ID: {admin.id})')
    return None, admin


def create_signup_identity(
    db: Session,
    full_name: str,
    email: str,
    organization_name: str,
    password: str,
) -> tuple[Tenant, TenantMember]:
    raise ValueError("Public signup is disabled.")


def bootstrap_super_admin(
    db: Session,
    full_name: str,
    email: str,
    password: str,
    organization_name: str = "VisionPass Platform",
) -> tuple[Tenant | None, SuperAdmin]:
    if has_super_admin(db):
        raise ValueError("SUPER_ADMIN already exists.")

    return create_first_super_admin(
        db=db,
        full_name=full_name,
        email=email,
        organization_name=organization_name,
        password=password,
    )


def change_user_password(db: Session, user: Any, current_password: str, new_password: str) -> Any:
    if not verify_password(current_password, user.password_hash):
        raise ValueError("Current password is incorrect.")

    user.password_hash = hash_password(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f'OK PASSWORD UPDATED -- User: "{user.full_name}" (ID: {user.id})')
    return user

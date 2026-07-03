"""Admin data management helpers."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.security import hash_password
from app.models.alert import Alert
from app.models.auth_session import AuthSession
from app.models.camera import Camera
from app.models.cv_feature import CvFeature
from app.models.tenant import Tenant
from app.models.user import User
from app.services.feature_flag_service import list_enabled_modules, set_tenant_modules
from app.services.tenant_service import create_tenant

logger = get_logger("admins")


def build_tenant_code(slug: str) -> str:
    parts = [segment[:3].upper() for segment in slug.split("-") if segment]
    if not parts:
        return slug.upper()[:12] or "TENANT"
    return "-".join(parts)[:12]


def get_primary_admin(db: Session, tenant_id: str) -> User | None:
    return (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.role == "tenant_admin", User.is_deleted.is_(False))
        .order_by(User.created_at.asc())
        .one_or_none()
    )


def _tenant_payload(db: Session, tenant: Tenant) -> dict:
    enabled_modules = list_enabled_modules(db, tenant.id)
    admin = get_primary_admin(db, tenant.id)
    user_count = db.query(User.id).filter(User.tenant_id == tenant.id, User.is_deleted.is_(False)).count()
    return {
        "id": tenant.id,
        "name": tenant.name,
        "slug": tenant.slug,
        "code": build_tenant_code(tenant.slug),
        "plan": tenant.plan,
        "status": tenant.status,
        "industry": tenant.industry,
        "logo_url": tenant.logo_url,
        "address": tenant.address,
        "admin_name": None if admin is None else admin.full_name,
        "admin_email": None if admin is None else admin.email,
        "phone": None if admin is None else admin.phone,
        "max_users": tenant.max_users,
        "max_devices": tenant.max_devices,
        "features_count": len(enabled_modules),
        "enabled_modules": enabled_modules,
        "users": user_count,
        # Physical sites are not a persisted MVP resource.
        "sites": 0,
        "alerts_today": db.query(Alert.id).filter(
            Alert.tenant_id == tenant.id,
            func.date(Alert.created_at) == datetime.now(timezone.utc).date(),
        ).count(),
        "cameras": db.query(Camera.id).filter(Camera.tenant_id == tenant.id).count(),
        "created_at": tenant.created_at,
        "updated_at": tenant.updated_at,
    }


def list_admin_tenants(db: Session) -> list[dict]:
    tenants = db.query(Tenant).filter(Tenant.is_deleted.is_(False)).order_by(Tenant.created_at.desc()).all()
    return [_tenant_payload(db, tenant) for tenant in tenants]


def get_admin_tenant(db: Session, tenant_id: str) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_deleted.is_(False)).one_or_none()
    if tenant is None:
        return None
    return _tenant_payload(db, tenant)


def get_admin_dashboard_summary(db: Session) -> dict:
    total_tenants = db.query(Tenant.id).filter(Tenant.is_deleted.is_(False)).count()
    active_tenants = db.query(Tenant.id).filter(Tenant.is_deleted.is_(False), Tenant.status == "active").count()
    total_tenant_admins = db.query(User.id).filter(User.is_deleted.is_(False), User.role == "tenant_admin").count()
    total_users = db.query(User.id).filter(User.is_deleted.is_(False)).count()
    total_features = db.query(CvFeature.id).count()
    active_sessions = (
        db.query(AuthSession.id)
        .filter(AuthSession.revoked_at.is_(None), AuthSession.expires_at > datetime.now(timezone.utc))
        .count()
    )
    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_tenant_admins": total_tenant_admins,
        "total_users": total_users,
        "total_features": total_features,
        "active_sessions": active_sessions,
    }


def get_admin_tenant_details(db: Session, tenant_id: str) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_deleted.is_(False)).one_or_none()
    if tenant is None:
        return None

    payload = _tenant_payload(db, tenant)
    admins = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.role == "tenant_admin", User.is_deleted.is_(False))
        .order_by(User.created_at.asc())
        .all()
    )
    users = (
        db.query(User)
        .filter(User.tenant_id == tenant.id, User.role == "user", User.is_deleted.is_(False))
        .order_by(User.created_at.asc())
        .all()
    )
    active_feature_codes = set(payload["enabled_modules"])
    assigned_features = [feature for feature in db.query(CvFeature).filter(CvFeature.status == "active").all() if feature.feature_code in active_feature_codes]
    latest_login = db.query(func.max(User.last_login_at)).filter(User.tenant_id == tenant.id).scalar()
    return {
        "tenant": payload,
        "admins": admins,
        "users": users,
        "assigned_features": assigned_features,
        "activity_summary": {
            "total_users": len(admins) + len(users),
            "tenant_admins": len(admins),
            "assigned_features": len(active_feature_codes),
            "enabled_features": len(active_feature_codes),
            "active_users": db.query(User.id).filter(User.tenant_id == tenant.id, User.is_active.is_(True), User.is_deleted.is_(False)).count(),
            "has_recent_login": 1 if latest_login is not None else 0,
        },
    }


def create_admin_tenant(
    db: Session,
    full_name: str,
    email: str,
    phone: str | None,
    password: str,
    organization_name: str,
    slug: str | None,
    logo_url: str | None,
    address: str | None,
    status: str,
    industry: str,
    max_users: int,
    max_devices: int,
    enabled_modules: list[str],
) -> dict:
    tenant_slug = slug or organization_name
    logger.info(f'>>> CREATE TENANT REQUEST -- by Admin: "{full_name}" | Email: {email}')
    tenant = create_tenant(
        db=db,
        name=organization_name,
        slug=tenant_slug,
        status=status,
        plan="basic",
        industry=industry,
        max_users=max_users,
        max_devices=max_devices,
        logo_url=logo_url,
        address=address,
    )
    user = User(
        tenant_id=tenant.id,
        email=email.lower().strip(),
        phone=phone.strip() if phone else None,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        role="tenant_admin",
        is_active=True,
        is_deleted=False,
        status="active",
    )
    db.add(user)
    db.commit()
    set_tenant_modules(db, tenant.id, enabled_modules, updated_by=user.id)
    db.refresh(tenant)
    db.refresh(user)
    logger.info(f'OK TENANT ADMIN CREATED -- ID: {user.id} | Email: {user.email}')
    return _tenant_payload(db, tenant)


def update_admin_tenant(
    db: Session,
    tenant_id: str,
    *,
    name: str | None = None,
    slug: str | None = None,
    logo_url: str | None = None,
    address: str | None = None,
    status: str | None = None,
    industry: str | None = None,
    admin_name: str | None = None,
    admin_email: str | None = None,
    phone: str | None = None,
    max_users: int | None = None,
    max_devices: int | None = None,
    enabled_modules: list[str] | None = None,
) -> dict | None:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_deleted.is_(False)).one_or_none()
    if tenant is None:
        return None

    logger.info(f'>>> UPDATE TENANT -- ID: {tenant_id} | Org: "{tenant.name}"')
    admin = get_primary_admin(db, tenant.id)

    if name is not None:
        tenant.name = name
    if slug is not None:
        tenant.slug = slug
    if logo_url is not None:
        tenant.logo_url = logo_url
    if address is not None:
        tenant.address = address
    if status is not None:
        tenant.status = status
    if industry is not None:
        tenant.industry = industry
    if max_users is not None:
        tenant.max_users = max_users
    if max_devices is not None:
        tenant.max_devices = max_devices
    if admin is not None:
        if admin_name is not None:
            admin.full_name = admin_name.strip()
        if admin_email is not None:
            normalized_email = admin_email.lower().strip()
            existing = db.query(User).filter(User.email == normalized_email, User.id != admin.id).one_or_none()
            if existing is not None:
                raise ValueError("Email already exists")
            admin.email = normalized_email
        if phone is not None:
            admin.phone = phone.strip() or None
    if enabled_modules is not None:
        set_tenant_modules(db, tenant.id, enabled_modules, updated_by=admin.id if admin else None)
    db.commit()
    db.refresh(tenant)
    if admin is not None:
        db.refresh(admin)
    logger.info(f'OK TENANT UPDATED -- ID: {tenant.id} | Org: "{tenant.name}"')
    return _tenant_payload(db, tenant)


def delete_admin_tenant(db: Session, tenant_id: str) -> bool:
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_deleted.is_(False)).one_or_none()
    if tenant is None:
        return False
    logger.warning(f'>>> SOFT DELETE TENANT -- Tenant: "{tenant.name}" (ID: {tenant.id})')
    tenant.is_deleted = True
    tenant.status = "inactive"
    db.commit()
    logger.warning(f'WARN TENANT MARKED DELETED -- ID: {tenant.id} | Org: "{tenant.name}"')
    return True

"""Tenant-admin scoped dashboard helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.feature import Feature
from app.models.user import User
from app.services.feature_flag_service import list_enabled_modules, list_enabled_member_modules, set_member_modules
from app.services.user_service import create_tenant_user, delete_tenant_user, list_tenant_users, update_tenant_user


def list_tenant_admin_members(db: Session, tenant_id: str) -> list[User]:
    return list_tenant_users(db, tenant_id)


def get_tenant_admin_dashboard_summary(db: Session, tenant_id: str) -> dict:
    members = list_tenant_admin_members(db, tenant_id)
    tenant_admins = [member for member in members if member.role == 'tenant_admin' and not member.is_deleted]
    users = [member for member in members if member.role == 'user' and not member.is_deleted]
    enabled_features = list_enabled_modules(db, tenant_id)
    return {
        'total_members': len([member for member in members if not member.is_deleted]),
        'tenant_admins': len(tenant_admins),
        'users': len(users),
        'enabled_features': len(enabled_features),
    }


def list_tenant_admin_features(db: Session, tenant_id: str) -> list[dict]:
    enabled_codes = set(list_enabled_modules(db, tenant_id))
    if not enabled_codes:
        return []
    features = db.query(Feature).filter(Feature.feature_code.in_(enabled_codes), Feature.status == 'active').order_by(Feature.feature_name.asc()).all()
    return [
        {
            'feature_name': feature.feature_name,
            'feature_code': feature.feature_code,
            'description': feature.description,
        }
        for feature in features
    ]


def list_tenant_member_features(db: Session, tenant_id: str, member_id: str) -> list[str]:
    return list_enabled_member_modules(db, tenant_id, member_id)


def create_tenant_admin_member(
    db: Session,
    tenant_id: str,
    *,
    full_name: str,
    email: str,
    password: str,
    role: str,
    status: str,
    feature_codes: list[str] | None = None,
) -> User:
    feature_codes = feature_codes or []
    enabled_features = set(list_enabled_modules(db, tenant_id))
    invalid_codes = sorted({code for code in feature_codes if code not in enabled_features})
    if invalid_codes:
        raise ValueError("Features must already be enabled for the tenant: " + ", ".join(invalid_codes))

    member = create_tenant_user(
        db,
        tenant_id,
        full_name=full_name,
        email=email,
        password=password,
        role=role,
        is_active=status == 'active',
    )
    if feature_codes:
        set_member_modules(db, tenant_id, member.id, feature_codes, updated_by=None)
    return member


def update_tenant_admin_member(
    db: Session,
    tenant_id: str,
    member_id: str,
    *,
    full_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    role: str | None = None,
    status: str | None = None,
    feature_codes: list[str] | None = None,
) -> User | None:
    if feature_codes is not None:
        enabled_features = set(list_enabled_modules(db, tenant_id))
        invalid_codes = sorted({code for code in feature_codes if code not in enabled_features})
        if invalid_codes:
            raise ValueError("Features must already be enabled for the tenant: " + ", ".join(invalid_codes))

    member = update_tenant_user(
        db,
        tenant_id,
        member_id,
        full_name=full_name,
        email=email,
        password=password,
        role=role,
        is_active=None if status is None else status == 'active',
    )
    if member is None:
        return None
    if feature_codes is not None:
        set_member_modules(db, tenant_id, member_id, feature_codes, updated_by=None)
    return member


def delete_tenant_admin_member(db: Session, tenant_id: str, member_id: str) -> bool:
    return delete_tenant_user(db, tenant_id, member_id)

"""Tenant user service."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.core.security import hash_password
from app.models.user import User

logger = get_logger("tenant_users")

ALLOWED_TENANT_ROLES = {
    "tenant_admin",
    "user",
}


def normalize_tenant_role(role: str) -> str:
    normalized = role.strip().lower()
    if normalized not in ALLOWED_TENANT_ROLES:
        raise ValueError("Invalid tenant role")
    return normalized


def list_tenant_users(db: Session, tenant_id: str) -> list[User]:
    return (
        db.query(User)
        .filter(
            User.tenant_id == tenant_id,
            User.is_deleted.is_(False),
            User.role.in_(sorted(ALLOWED_TENANT_ROLES)),
        )
        .order_by(User.created_at.desc())
        .all()
    )


def get_tenant_user(db: Session, tenant_id: str, user_id: str) -> User | None:
    return (
        db.query(User)
        .filter(
            User.tenant_id == tenant_id,
            User.id == user_id,
            User.is_deleted.is_(False),
            User.role.in_(sorted(ALLOWED_TENANT_ROLES)),
        )
        .one_or_none()
    )


def create_tenant_user(
    db: Session,
    tenant_id: str,
    *,
    created_by: User | None = None,
    full_name: str,
    email: str,
    password: str,
    phone: str | None = None,
    role: str = "user",
    department: str | None = None,
    designation: str | None = None,
    employee_id: str | None = None,
    access_zones: list[str] | None = None,
    is_active: bool = True,
    face_enrolled: bool = False,
    notes: str | None = None,
) -> User:
    normalized_role = normalize_tenant_role(role)
    normalized_email = email.lower().strip()
    existing = db.query(User).filter(User.email == normalized_email).one_or_none()
    if existing is not None:
        raise ValueError("Email already exists")

    logger.info(f'>>> CREATE TENANT USER -- Tenant: {tenant_id} | Email: {normalized_email} | Role: {normalized_role}')

    user = User(
        tenant_id=tenant_id,
        email=normalized_email,
        phone=phone.strip() if phone else None,
        password_hash=hash_password(password),
        full_name=full_name.strip(),
        role=normalized_role,
        department=department.strip() if department else None,
        designation=designation.strip() if designation else None,
        employee_id=employee_id.strip() if employee_id else None,
        access_zones=access_zones or [],
        is_active=is_active,
        face_enrolled=face_enrolled,
        notes=notes.strip() if notes else None,
        created_by=None if created_by is None else created_by.id,
        last_login_at=None,
        is_deleted=False,
        status="active" if is_active else "inactive",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f'OK TENANT USER CREATED -- ID: {user.id} | Name: "{user.full_name}"')
    return user


def update_tenant_user(
    db: Session,
    tenant_id: str,
    user_id: str,
    *,
    full_name: str | None = None,
    email: str | None = None,
    password: str | None = None,
    phone: str | None = None,
    role: str | None = None,
    department: str | None = None,
    designation: str | None = None,
    employee_id: str | None = None,
    access_zones: list[str] | None = None,
    is_active: bool | None = None,
    face_enrolled: bool | None = None,
    notes: str | None = None,
) -> User | None:
    user = get_tenant_user(db, tenant_id, user_id)
    if user is None:
        return None

    logger.info(f'>>> UPDATE TENANT USER -- Tenant: {tenant_id} | User ID: {user_id}')

    if full_name is not None:
        user.full_name = full_name.strip()
    if email is not None:
        normalized_email = email.lower().strip()
        existing = (
            db.query(User)
            .filter(User.email == normalized_email, User.id != user.id)
            .one_or_none()
        )
        if existing is not None:
            raise ValueError("Email already exists")
        user.email = normalized_email
    if password is not None and password.strip():
        user.password_hash = hash_password(password)
    if phone is not None:
        user.phone = phone.strip() or None
    if role is not None:
        user.role = normalize_tenant_role(role)
    if department is not None:
        user.department = department.strip() or None
    if designation is not None:
        user.designation = designation.strip() or None
    if employee_id is not None:
        user.employee_id = employee_id.strip() or None
    if access_zones is not None:
        user.access_zones = access_zones
    if is_active is not None:
        user.is_active = is_active
        user.status = "active" if is_active else "inactive"
    if face_enrolled is not None:
        user.face_enrolled = face_enrolled
    if notes is not None:
        user.notes = notes.strip() or None

    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)
    logger.info(f'OK TENANT USER UPDATED -- ID: {user.id} | Active: {user.is_active}')
    return user


def delete_tenant_user(db: Session, tenant_id: str, user_id: str) -> bool:
    user = get_tenant_user(db, tenant_id, user_id)
    if user is None:
        return False
    logger.warning(f'>>> SOFT DELETE TENANT USER -- Tenant: {tenant_id} | User ID: {user_id}')
    user.is_active = False
    user.is_deleted = True
    user.status = "inactive"
    user.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.warning(f'WARN TENANT USER MARKED DELETED -- ID: {user.id} | Email: {user.email}')
    return True

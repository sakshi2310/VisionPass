"""Application bootstrap helpers."""

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.super_admin import SuperAdmin
from app.models.tenant import Tenant
from app.models.tenant_feature import TenantFeature
from app.models.tenant_member import TenantMember
from app.models.member_feature import MemberFeature
from app.services.cv_feature_service import seed_default_master_features
from app.services.feature_flag_service import set_member_modules, set_tenant_modules
from app.services.tenant_service import create_tenant

DEMO_SUPER_ADMIN_EMAIL = "admin@gmail.com"
DEMO_SUPER_ADMIN_PASSWORD = "admin@123"
DEMO_TENANT_SLUG = "visionpass-demo"
DEMO_TENANT_NAME = "VisionPass Demo Tenant"
DEMO_TENANT_ADMIN_EMAIL = "tenant.admin@visionpass.test"
DEMO_TENANT_ADMIN_PASSWORD = "TenantAdmin@123"
DEMO_TENANT_USER_EMAIL = "normal.user@visionpass.test"
DEMO_TENANT_USER_PASSWORD = "User@123456"
DEMO_FEATURE_CODES = ["face_recognition", "object_detection", "attendance"]
DEMO_USER_FEATURE_CODES = ["face_recognition", "attendance"]


def _upsert_super_admin(db: Session) -> SuperAdmin:
    admin = db.query(SuperAdmin).filter(SuperAdmin.email == DEMO_SUPER_ADMIN_EMAIL).one_or_none()
    if admin is not None:
        return admin

    admin = SuperAdmin(
        email=DEMO_SUPER_ADMIN_EMAIL,
        password_hash=hash_password(DEMO_SUPER_ADMIN_PASSWORD),
        full_name="Super Admin",
        status="active",
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def _upsert_demo_tenant(db: Session) -> Tenant:
    tenant = db.query(Tenant).filter(Tenant.slug == DEMO_TENANT_SLUG, Tenant.is_deleted.is_(False)).one_or_none()
    if tenant is not None:
        return tenant

    tenant = create_tenant(
        db=db,
        name=DEMO_TENANT_NAME,
        slug=DEMO_TENANT_SLUG,
        status="active",
        plan="basic",
        industry="Security",
        max_users=100,
        max_devices=20,
        address="Demo Campus",
    )
    db.commit()
    db.refresh(tenant)
    return tenant


def _upsert_tenant_member(
    db: Session,
    *,
    tenant_id: str,
    email: str,
    full_name: str,
    password: str,
    role: str,
) -> TenantMember:
    member = (
        db.query(TenantMember)
        .filter(TenantMember.tenant_id == tenant_id, TenantMember.email == email.lower().strip(), TenantMember.is_deleted.is_(False))
        .one_or_none()
    )
    if member is not None:
        member.full_name = full_name
        member.role = role
        member.status = "active"
        member.is_active = True
        member.password_hash = hash_password(password)
        db.commit()
        db.refresh(member)
        return member

    member = TenantMember(
        tenant_id=tenant_id,
        email=email.lower().strip(),
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        status="active",
        is_active=True,
        is_deleted=False,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def seed_default_admin(db: Session) -> None:
    seed_default_master_features(db)
    _upsert_super_admin(db)
    tenant = _upsert_demo_tenant(db)
    tenant_admin = _upsert_tenant_member(
        db,
        tenant_id=tenant.id,
        email=DEMO_TENANT_ADMIN_EMAIL,
        full_name="Demo Tenant Admin",
        password=DEMO_TENANT_ADMIN_PASSWORD,
        role="tenant_admin",
    )
    tenant_user = _upsert_tenant_member(
        db,
        tenant_id=tenant.id,
        email=DEMO_TENANT_USER_EMAIL,
        full_name="Demo Tenant User",
        password=DEMO_TENANT_USER_PASSWORD,
        role="user",
    )

    set_tenant_modules(db, tenant.id, DEMO_FEATURE_CODES, updated_by=tenant_admin.id)
    set_member_modules(db, tenant.id, tenant_admin.id, DEMO_FEATURE_CODES, updated_by=tenant_admin.id)
    set_member_modules(db, tenant.id, tenant_user.id, DEMO_USER_FEATURE_CODES, updated_by=tenant_admin.id)

"""Feature flag service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.models.feature import Feature
from app.models.member_feature import MemberFeature
from app.models.super_admin import SuperAdmin
from app.models.tenant_feature import TenantFeature
from app.models.tenant_member import TenantMember
from app.services.cv_feature_service import list_active_feature_codes

logger = get_logger("features")

DEFAULT_MODULES = (
    "attendance",
    "object_detection",
    "visitor_unknown",
)

MODULE_ALIASES = {
    "visitor_management": "visitor_unknown",
}


def _canonical_module_code(module_name: str) -> str:
    return MODULE_ALIASES.get(module_name, module_name)


def _split_updated_by(db: Session, updated_by: str | None) -> tuple[str | None, str | None]:
    if updated_by is None:
        return None, None
    if db.query(SuperAdmin.id).filter(SuperAdmin.id == updated_by).one_or_none() is not None:
        return updated_by, None
    return None, updated_by


def _active_feature_codes(db: Session) -> set[str]:
    active_codes = {_canonical_module_code(code) for code in list_active_feature_codes(db)}
    if not active_codes:
        active_codes = set(DEFAULT_MODULES)
    return active_codes


def _tenant_enabled_codes(db: Session, tenant_id: str | None) -> set[str]:
    if tenant_id is None:
        return set()
    active_codes = _active_feature_codes(db)
    rows = (
        db.query(TenantFeature.feature_code)
        .filter(TenantFeature.tenant_id == tenant_id, TenantFeature.enabled.is_(True))
        .all()
    )
    return {_canonical_module_code(feature_code) for (feature_code,) in rows if _canonical_module_code(feature_code) in active_codes}


def _member_enabled_codes(db: Session, tenant_id: str | None, member_id: str | None) -> set[str]:
    if tenant_id is None or member_id is None:
        return set()
    tenant_enabled = _tenant_enabled_codes(db, tenant_id)
    rows = (
        db.query(MemberFeature.feature_code)
        .join(TenantMember, TenantMember.id == MemberFeature.tenant_member_id)
        .filter(
            TenantMember.tenant_id == tenant_id,
            TenantMember.id == member_id,
            TenantMember.is_deleted.is_(False),
            MemberFeature.enabled.is_(True),
        )
        .all()
    )
    member_enabled = {
        _canonical_module_code(feature_code)
        for (feature_code,) in rows
        if _canonical_module_code(feature_code) in _active_feature_codes(db)
    }
    return member_enabled & tenant_enabled if tenant_enabled else member_enabled


def list_tenant_flags(db: Session, tenant_id: str) -> list[TenantFeature]:
    return (
        db.query(TenantFeature)
        .filter(TenantFeature.tenant_id == tenant_id)
        .order_by(TenantFeature.feature_code.asc())
        .all()
    )


def list_tenant_module_views(db: Session, tenant_id: str) -> list[TenantFeature]:
    active_codes = _active_feature_codes(db)
    existing_flags = {_canonical_module_code(flag.feature_code): flag for flag in list_tenant_flags(db, tenant_id)}
    ordered_flags: list[TenantFeature] = []
    for module_name in active_codes:
        flag = existing_flags.get(module_name)
        if flag is None:
            flag = TenantFeature(
                tenant_id=tenant_id,
                feature_code=module_name,
                enabled=False,
                config=None,
                updated_by_super_admin_id=None,
                updated_by_member_id=None,
            )
            flag.id = None
        ordered_flags.append(flag)
    return ordered_flags


def list_enabled_modules(db: Session, tenant_id: str | None) -> list[str]:
    return sorted(_tenant_enabled_codes(db, tenant_id))


def list_enabled_member_modules(db: Session, tenant_id: str | None, member_id: str | None) -> list[str]:
    return sorted(_member_enabled_codes(db, tenant_id, member_id))


def get_flag(db: Session, tenant_id: str, module_name: str) -> TenantFeature | None:
    module_name = _canonical_module_code(module_name)
    return (
        db.query(TenantFeature)
        .filter(
            TenantFeature.tenant_id == tenant_id,
            TenantFeature.feature_code == module_name,
        )
        .one_or_none()
    )


def upsert_flag(
    db: Session,
    tenant_id: str,
    module_name: str,
    enabled: bool,
    config: dict | None = None,
    updated_by: str | None = None,
) -> TenantFeature:
    module_name = _canonical_module_code(module_name)
    logger.info(f'>>> TOGGLE MODULE -- Tenant: {tenant_id} | Module: {module_name} | Enabled: {enabled}')
    updated_by_super_admin_id, updated_by_member_id = _split_updated_by(db, updated_by)
    flag = get_flag(db, tenant_id, module_name)
    if flag is None:
        flag = TenantFeature(
            tenant_id=tenant_id,
            feature_code=module_name,
            enabled=enabled,
            config=config,
            updated_by_super_admin_id=updated_by_super_admin_id,
            updated_by_member_id=updated_by_member_id,
        )
        db.add(flag)
    else:
        flag.enabled = enabled
        flag.config = config
        flag.updated_by_super_admin_id = updated_by_super_admin_id
        flag.updated_by_member_id = updated_by_member_id
    db.commit()
    db.refresh(flag)
    logger.info(f'OK MODULE UPDATED -- Tenant: {tenant_id} | Module: {module_name} | Enabled: {flag.enabled}')
    return flag


def set_tenant_modules(
    db: Session,
    tenant_id: str,
    enabled_modules: list[str],
    updated_by: str | None = None,
) -> list[TenantFeature]:
    logger.info(f'>>> REPLACE TENANT MODULES -- Tenant: {tenant_id} | Enabled modules: {enabled_modules}')
    updated_by_super_admin_id, updated_by_member_id = _split_updated_by(db, updated_by)
    active_codes = _active_feature_codes(db)
    normalized_modules = [_canonical_module_code(module_name) for module_name in enabled_modules]
    enabled_set = {module_name for module_name in normalized_modules if module_name in active_codes}
    ordered_modules = [module_name for module_name in active_codes if module_name in normalized_modules or module_name not in enabled_set]

    updated_flags: list[TenantFeature] = []
    for module_name in ordered_modules:
        flag = get_flag(db, tenant_id, module_name)
        if flag is None:
            flag = TenantFeature(
                tenant_id=tenant_id,
                feature_code=module_name,
                enabled=module_name in enabled_set,
                config=None,
                updated_by_super_admin_id=updated_by_super_admin_id,
                updated_by_member_id=updated_by_member_id,
            )
            db.add(flag)
        else:
            flag.enabled = module_name in enabled_set
            flag.updated_by_super_admin_id = updated_by_super_admin_id
            flag.updated_by_member_id = updated_by_member_id
        updated_flags.append(flag)

    db.commit()
    for flag in updated_flags:
        db.refresh(flag)
    logger.info(f'OK TENANT MODULES UPDATED -- Tenant: {tenant_id} | Count: {len(updated_flags)}')
    return updated_flags


def set_member_modules(
    db: Session,
    tenant_id: str,
    member_id: str,
    feature_codes: list[str],
    updated_by: str | None = None,
    *,
    commit: bool = True,
) -> list[MemberFeature]:
    logger.info(f'>>> REPLACE MEMBER MODULES -- Tenant: {tenant_id} | Member: {member_id} | Features: {feature_codes}')
    member = (
        db.query(TenantMember)
        .filter(
            TenantMember.id == member_id,
            TenantMember.tenant_id == tenant_id,
            TenantMember.is_deleted.is_(False),
        )
        .one_or_none()
    )
    if member is None:
        raise ValueError("Member not found")

    active_codes = _active_feature_codes(db)
    tenant_enabled = _tenant_enabled_codes(db, tenant_id)
    normalized_codes = [_canonical_module_code(code.strip().lower()) for code in feature_codes if code and code.strip()]
    invalid_codes = sorted({code for code in normalized_codes if code not in active_codes or code not in tenant_enabled})
    if invalid_codes:
        raise ValueError("Features must already be enabled for the tenant: " + ", ".join(invalid_codes))

    db.query(MemberFeature).filter(MemberFeature.tenant_member_id == member_id).delete(synchronize_session=False)
    db.flush()

    updated_rows: list[MemberFeature] = []
    unique_codes = sorted(set(normalized_codes))
    for code in unique_codes:
        row = MemberFeature(
            tenant_member_id=member_id,
            feature_code=code,
            enabled=True,
            config=None,
        )
        db.add(row)
        updated_rows.append(row)

    if commit:
        db.commit()
        for row in updated_rows:
            db.refresh(row)
    logger.info(f'OK MEMBER MODULES UPDATED -- Tenant: {tenant_id} | Member: {member_id} | Count: {len(updated_rows)}')
    return updated_rows


def ensure_module_access(db: Session, current_user, module_name: str) -> bool:
    module_name = _canonical_module_code(module_name)
    role = str(getattr(current_user, "role", "")).strip().lower()
    if role == "super_admin":
        return True

    tenant_id = getattr(current_user, "tenant_id", None)
    member_id = getattr(current_user, "id", None)
    if tenant_id is None or member_id is None:
        return False

    active_codes = _active_feature_codes(db)
    if module_name not in active_codes:
        return False

    tenant_enabled = _tenant_enabled_codes(db, tenant_id)
    if role in {"tenant_admin", "client_admin"}:
        return module_name in tenant_enabled

    member_enabled = _member_enabled_codes(db, tenant_id, member_id)
    return module_name in tenant_enabled and module_name in member_enabled

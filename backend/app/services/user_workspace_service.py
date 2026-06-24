"""User workspace helpers."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.feature import Feature
from app.models.member_feature import MemberFeature
from app.models.tenant import Tenant
from app.models.user import User
from app.services.feature_flag_service import list_enabled_modules

FEATURE_ROUTE_MAP: dict[str, str] = {
    'attendance': '/dashboard/attendance',
    'visitor_management': '/dashboard/visitors',
    'access_control': '/dashboard/access-control',
    'alerts': '/dashboard/alerts',
    'genai_assistant': '/dashboard/assistant',
    'analytics': '/dashboard/analytics',
}

FEATURE_MODULE_KEY_MAP: dict[str, str] = {
    'attendance': 'attendance',
    'visitor_management': 'visitor_classification',
    'access_control': 'access_control',
    'alerts': 'alerts',
    'genai_assistant': 'genai_assistant',
    'analytics': 'analytics',
}


def _list_allowed_feature_codes(db: Session, tenant_id: str, member_id: str) -> set[str]:
    tenant_enabled = set(list_enabled_modules(db, tenant_id))
    member_rows = (
        db.query(MemberFeature)
        .filter(MemberFeature.tenant_member_id == member_id)
        .order_by(MemberFeature.feature_code.asc())
        .all()
    )

    if member_rows:
        enabled_codes = {row.feature_code for row in member_rows if row.enabled}
        return enabled_codes & tenant_enabled if tenant_enabled else enabled_codes

    return tenant_enabled


def list_user_workspace_features(db: Session, tenant_id: str, member_id: str) -> list[dict]:
    allowed_codes = _list_allowed_feature_codes(db, tenant_id, member_id)
    if not allowed_codes:
        return []

    features = (
        db.query(Feature)
        .filter(Feature.feature_code.in_(allowed_codes), Feature.status == 'active')
        .order_by(Feature.feature_name.asc())
        .all()
    )

    return [
        {
            'feature_name': feature.feature_name,
            'feature_code': feature.feature_code,
            'description': feature.description,
            'module_key': FEATURE_MODULE_KEY_MAP.get(feature.feature_code),
            'route': FEATURE_ROUTE_MAP.get(feature.feature_code),
        }
        for feature in features
    ]


def get_user_workspace_dashboard(db: Session, tenant_id: str, member_id: str) -> dict:
    member = (
        db.query(User)
        .filter(User.tenant_id == tenant_id, User.id == member_id, User.is_deleted.is_(False))
        .one_or_none()
    )
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id, Tenant.is_deleted.is_(False)).one_or_none()
    if member is None or tenant is None:
        return {
            'summary': {
                'tenant_name': 'Unknown tenant',
                'member_name': 'Unknown member',
                'member_role': 'user',
                'tenant_id': tenant_id,
                'member_id': member_id,
                'profile_status': 'inactive',
                'assigned_features_count': 0,
                'open_modules_count': 0,
            },
            'profile': None,
            'features': [],
        }

    features = list_user_workspace_features(db, tenant_id, member_id)
    open_modules_count = sum(1 for feature in features if feature.get('route'))

    return {
        'summary': {
            'tenant_name': tenant.name,
            'member_name': member.full_name,
            'member_role': member.role,
            'tenant_id': tenant.id,
            'member_id': member.id,
            'profile_status': member.status,
            'assigned_features_count': len(features),
            'open_modules_count': open_modules_count,
        },
        'profile': member,
        'features': features,
    }

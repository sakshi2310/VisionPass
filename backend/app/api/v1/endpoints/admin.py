"""Super-admin routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, require_role
from app.core.logger import get_logger
from app.schemas.admin import AdminDashboardSummaryRead, AdminTenantCreate, AdminTenantDetailsRead, AdminTenantRead, AdminTenantUpdate
from app.schemas.attendance import AttendanceFaceSettingsRead, AttendanceFaceSettingsUpdate
from app.schemas.audit_log import AdminAuditLogListResponse, AdminAuditLogRead
from app.schemas.auth import AuthResponse, LoginRequest, TokenResponse
from app.schemas.cv_feature import CvFeatureCreate, CvFeatureListResponse, CvFeatureRead, CvFeatureUpdate
from app.schemas.user import UserRead
from app.services.admin_service import create_admin_tenant, delete_admin_tenant, get_admin_dashboard_summary, get_admin_tenant, get_admin_tenant_details, list_admin_tenants, update_admin_tenant
from app.services.audit_service import list_admin_audit_logs
from app.services.auth_service import authenticate_super_admin_login, issue_login_token
from app.services.cv_feature_service import create_master_feature, delete_master_feature, list_master_features, update_master_feature
from app.services.employee_service import get_or_create_face_settings, update_face_settings
from app.services.feature_flag_service import list_tenant_module_views, set_tenant_modules, upsert_flag

router = APIRouter()
logger = get_logger("admin")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(database_session)) -> AuthResponse:
    logger.info(f'>>> SUPER ADMIN LOGIN ATTEMPT -- email: {payload.email}')
    try:
        super_admin = authenticate_super_admin_login(db, payload.email, payload.password)
    except ValueError as exc:
        message = str(exc)
        if message == "Account inactive":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    access_token = issue_login_token(super_admin)
    logger.info(f'LOGIN SUCCESS -- Super Admin: "{super_admin.full_name}"')
    return AuthResponse(
        token=TokenResponse(access_token=access_token, token_type="bearer"),
        user=UserRead.model_validate(super_admin),
        tenant=None,
    )


@router.get("/summary", response_model=AdminDashboardSummaryRead)
def get_summary(
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminDashboardSummaryRead:
    return AdminDashboardSummaryRead.model_validate(get_admin_dashboard_summary(db))


@router.get("/tenants", response_model=list[AdminTenantRead])
def get_tenants(
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> list[AdminTenantRead]:
    return [AdminTenantRead.model_validate(tenant) for tenant in list_admin_tenants(db)]


@router.post("/tenants", response_model=AdminTenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant(
    payload: AdminTenantCreate,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminTenantRead:
    tenant = create_admin_tenant(
        db=db,
        full_name=payload.full_name,
        email=payload.email,
        company_email=payload.company_email,
        phone=payload.phone,
        password=payload.password,
        organization_name=payload.organization_name,
        slug=payload.slug,
        logo_url=payload.logo_url,
        address=payload.address,
        status=payload.status,
        industry=payload.industry,
        max_users=payload.max_users,
        max_devices=payload.max_devices,
        enabled_modules=payload.enabled_modules,
    )
    return AdminTenantRead.model_validate(tenant)


@router.delete("/tenants/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tenant(
    tenant_id: str,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> None:
    deleted = delete_admin_tenant(db, tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")


@router.get("/tenants/{tenant_id}", response_model=AdminTenantRead)
def get_tenant(
    tenant_id: str,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminTenantRead:
    tenant = get_admin_tenant(db, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return AdminTenantRead.model_validate(tenant)


@router.get("/tenants/{tenant_id}/details", response_model=AdminTenantDetailsRead)
def get_tenant_details(
    tenant_id: str,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminTenantDetailsRead:
    tenant = get_admin_tenant_details(db, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return AdminTenantDetailsRead.model_validate(tenant)


@router.get("/tenants/{tenant_id}/face-settings", response_model=AttendanceFaceSettingsRead)
def get_tenant_face_settings(
    tenant_id: str,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AttendanceFaceSettingsRead:
    settings = get_or_create_face_settings(db, tenant_id)
    return AttendanceFaceSettingsRead.model_validate(settings)


@router.put("/tenants/{tenant_id}/face-settings", response_model=AttendanceFaceSettingsRead)
def save_tenant_face_settings(
    tenant_id: str,
    payload: AttendanceFaceSettingsUpdate,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AttendanceFaceSettingsRead:
    settings = update_face_settings(
        db,
        tenant_id,
        face_match_threshold=payload.face_match_threshold,
        min_face_images=payload.min_face_images,
        recommended_face_images=payload.recommended_face_images,
        max_face_images=payload.max_face_images,
        min_face_size_px=payload.min_face_size_px,
        min_resolution_width=payload.min_resolution_width,
        min_resolution_height=payload.min_resolution_height,
        max_blur_score=payload.max_blur_score,
        min_brightness=payload.min_brightness,
        max_brightness=payload.max_brightness,
        embedding_model=payload.embedding_model,
        embedding_version=payload.embedding_version,
        embedding_dimension=payload.embedding_dimension,
        is_active=payload.is_active,
    )
    return AttendanceFaceSettingsRead.model_validate(settings)


@router.patch("/tenants/{tenant_id}", response_model=AdminTenantRead)
def patch_tenant(
    tenant_id: str,
    payload: AdminTenantUpdate,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminTenantRead:
    tenant = update_admin_tenant(
        db=db,
        tenant_id=tenant_id,
        name=payload.name,
        company_email=payload.company_email,
        slug=payload.slug,
        logo_url=payload.logo_url,
        address=payload.address,
        status=payload.status,
        industry=payload.industry,
        admin_name=payload.admin_name,
        admin_email=payload.admin_email,
        phone=payload.phone,
        max_users=payload.max_users,
        max_devices=payload.max_devices,
        enabled_modules=payload.enabled_modules,
    )
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    return AdminTenantRead.model_validate(tenant)


@router.get("/audit-logs", response_model=AdminAuditLogListResponse)
def get_audit_logs(
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> AdminAuditLogListResponse:
    return AdminAuditLogListResponse(logs=[AdminAuditLogRead.model_validate(log) for log in list_admin_audit_logs(db)])


@router.get("/features", response_model=CvFeatureListResponse)
def get_features(
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> CvFeatureListResponse:
    return CvFeatureListResponse(
        features=[
            CvFeatureRead.model_validate(feature)
            for feature in list_master_features(db, include_deleted=True)
        ]
    )


@router.post("/features", response_model=CvFeatureRead, status_code=status.HTTP_201_CREATED)
def create_feature(
    payload: CvFeatureCreate,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> CvFeatureRead:
    try:
        feature = create_master_feature(
            db,
            feature_name=payload.feature_name,
            feature_code=payload.feature_code,
            description=payload.description,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return CvFeatureRead.model_validate(feature)


@router.patch("/features/{feature_id}", response_model=CvFeatureRead)
def patch_feature(
    feature_id: str,
    payload: CvFeatureUpdate,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> CvFeatureRead:
    try:
        feature = update_master_feature(
            db,
            feature_id,
            feature_name=payload.feature_name,
            feature_code=payload.feature_code,
            description=payload.description,
            status=payload.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if feature is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found")
    return CvFeatureRead.model_validate(feature)


@router.delete("/features/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_feature(
    feature_id: str,
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> None:
    deleted = delete_master_feature(db, feature_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feature not found")

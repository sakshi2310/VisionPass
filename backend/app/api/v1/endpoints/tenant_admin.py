"""Tenant admin workspace routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.models.user import User
from app.schemas.tenant_admin import (
    TenantAdminDashboardSummary,
    TenantAdminFeatureListResponse,
    TenantAdminFeatureRead,
    TenantAdminMemberCreate,
    TenantAdminMemberFeatureCodesResponse,
    TenantAdminMemberFeaturesUpdate,
    TenantAdminMemberListResponse,
    TenantAdminMemberRead,
    TenantAdminMemberUpdate,
)
from app.services.tenant_admin_service import (
    create_tenant_admin_member,
    delete_tenant_admin_member,
    get_tenant_admin_dashboard_summary,
    list_tenant_admin_features,
    list_tenant_admin_members,
    list_tenant_member_features,
    update_tenant_admin_member,
)

router = APIRouter()


@router.get('/dashboard', response_model=TenantAdminDashboardSummary)
def get_dashboard_summary(
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminDashboardSummary:
    return TenantAdminDashboardSummary.model_validate(get_tenant_admin_dashboard_summary(db, current_admin.tenant_id))


@router.get('/members', response_model=TenantAdminMemberListResponse)
def get_members(
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminMemberListResponse:
    members = list_tenant_admin_members(db, current_admin.tenant_id)
    return TenantAdminMemberListResponse(members=[TenantAdminMemberRead.model_validate(member) for member in members])


@router.post('/members', response_model=TenantAdminMemberRead, status_code=status.HTTP_201_CREATED)
def create_member(
    payload: TenantAdminMemberCreate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminMemberRead:
    try:
        member = create_tenant_admin_member(
            db,
            current_admin.tenant_id,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            status=payload.status,
            feature_codes=payload.feature_codes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return TenantAdminMemberRead.model_validate(member)


@router.patch('/members/{member_id}', response_model=TenantAdminMemberRead)
def update_member(
    member_id: str,
    payload: TenantAdminMemberUpdate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminMemberRead:
    try:
        member = update_tenant_admin_member(
            db,
            current_admin.tenant_id,
            member_id,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            status=payload.status,
            feature_codes=payload.feature_codes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')
    return TenantAdminMemberRead.model_validate(member)


@router.delete('/members/{member_id}', status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    member_id: str,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_tenant_admin_member(db, current_admin.tenant_id, member_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')


@router.get('/members/{member_id}/features', response_model=TenantAdminMemberFeatureCodesResponse)
def get_member_features(
    member_id: str,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminMemberFeatureCodesResponse:
    return TenantAdminMemberFeatureCodesResponse(
        feature_codes=list_tenant_member_features(db, current_admin.tenant_id, member_id),
    )


@router.put('/members/{member_id}/features', response_model=TenantAdminMemberFeatureCodesResponse)
def update_member_features(
    member_id: str,
    payload: TenantAdminMemberFeaturesUpdate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminMemberFeatureCodesResponse:
    try:
        member = update_tenant_admin_member(
            db,
            current_admin.tenant_id,
            member_id,
            feature_codes=payload.feature_codes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Member not found')
    return TenantAdminMemberFeatureCodesResponse(
        feature_codes=list_tenant_member_features(db, current_admin.tenant_id, member_id),
    )


@router.get('/features', response_model=TenantAdminFeatureListResponse)
def get_features(
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantAdminFeatureListResponse:
    features = list_tenant_admin_features(db, current_admin.tenant_id)
    return TenantAdminFeatureListResponse(features=[TenantAdminFeatureRead.model_validate(feature) for feature in features])

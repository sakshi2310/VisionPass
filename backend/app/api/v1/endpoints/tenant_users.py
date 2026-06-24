"""Tenant admin user management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.core.logger import get_logger
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.user import TenantUserCreate, TenantUserListResponse, TenantUserRead, TenantUserUpdate
from app.services.user_service import create_tenant_user, delete_tenant_user, list_tenant_users, update_tenant_user

router = APIRouter()
logger = get_logger("tenant_users")


@router.get("", response_model=TenantUserListResponse)
def get_users(
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantUserListResponse:
    return TenantUserListResponse(users=[TenantUserRead.model_validate(user) for user in list_tenant_users(db, current_admin.tenant_id)])


@router.post("/create", response_model=TenantUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: TenantUserCreate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantUserRead:
    tenant = db.query(Tenant).filter(Tenant.id == current_admin.tenant_id).one_or_none()
    logger.info(f'>>> CREATE TENANT USER -- by Tenant Admin: "{current_admin.full_name}"')
    logger.info(f'Tenant: "{tenant.name if tenant is not None else current_admin.tenant_id}"')
    logger.info(f'User Email: {payload.email}')
    logger.info(f'Role: {payload.role}')
    logger.info('Password: [HIDDEN]')
    try:
        user = create_tenant_user(
            db,
            current_admin.tenant_id,
            created_by=current_admin,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            phone=payload.phone,
            role=payload.role,
            department=payload.department,
            designation=payload.designation,
            employee_id=payload.employee_id,
            access_zones=payload.access_zones,
            is_active=payload.is_active,
            face_enrolled=payload.face_enrolled,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    logger.info(f'TENANT USER CREATED -- ID: {user.id}')
    return TenantUserRead.model_validate(user)


@router.get("/{user_id}", response_model=TenantUserRead)
def get_user(
    user_id: str,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantUserRead:
    user = next((item for item in list_tenant_users(db, current_admin.tenant_id) if item.id == user_id), None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return TenantUserRead.model_validate(user)


@router.patch("/{user_id}", response_model=TenantUserRead)
def patch_user(
    user_id: str,
    payload: TenantUserUpdate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantUserRead:
    try:
        user = update_tenant_user(
            db,
            current_admin.tenant_id,
            user_id,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            phone=payload.phone,
            role=payload.role,
            department=payload.department,
            designation=payload.designation,
            employee_id=payload.employee_id,
            access_zones=payload.access_zones,
            is_active=payload.is_active,
            face_enrolled=payload.face_enrolled,
            notes=payload.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return TenantUserRead.model_validate(user)


@router.patch("/{user_id}/status", response_model=TenantUserRead)
def update_status(
    user_id: str,
    payload: TenantUserUpdate,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> TenantUserRead:
    try:
        user = update_tenant_user(
            db,
            current_admin.tenant_id,
            user_id,
            is_active=payload.is_active,
            face_enrolled=payload.face_enrolled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return TenantUserRead.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_user(
    user_id: str,
    db: Session = Depends(database_session),
    current_admin: User = Depends(get_current_tenant_admin),
) -> None:
    deleted = delete_tenant_user(db, current_admin.tenant_id, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

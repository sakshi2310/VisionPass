"""Auth routes."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_user
from app.core.logger import get_logger
from app.schemas.auth import (
    AuthResponse,
    BootstrapRequest,
    BootstrapStatusResponse,
    ChangePasswordRequest,
    LoginRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.models.tenant import Tenant
from app.services.auth_service import (
    authenticate_login,
    bootstrap_super_admin,
    build_display_role,
    change_user_password,
    has_super_admin,
    issue_login_token,
)
from app.services.feature_flag_service import list_enabled_member_modules, list_enabled_modules

router = APIRouter()
logger = get_logger("auth")


@router.get("/bootstrap-status", response_model=BootstrapStatusResponse)
def bootstrap_status(db: Session = Depends(database_session)) -> BootstrapStatusResponse:
    return BootstrapStatusResponse(setup_required=not has_super_admin(db))


@router.post("/bootstrap", response_model=AuthResponse)
def bootstrap(
    payload: BootstrapRequest,
    db: Session = Depends(database_session),
) -> AuthResponse:
    logger.info(f'>>> BOOTSTRAP REQUEST -- Email: {payload.email}')
    try:
        tenant, user = bootstrap_super_admin(
            db=db,
            full_name=payload.full_name,
            email=payload.email,
            password=payload.password,
            organization_name=payload.organization_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc

    access_token = issue_login_token(user)
    logger.info(f'OK BOOTSTRAP SUCCESS -- Admin: "{user.full_name}" (ID: {user.id})')
    return AuthResponse(
        token=TokenResponse(access_token=access_token),
        user=UserRead.model_validate(user),
        tenant=tenant,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(database_session),
) -> AuthResponse:
    logger.info(f'>>> LOGIN ATTEMPT -- email: {payload.email}')
    try:
        tenant, user = authenticate_login(db, payload.email, payload.password)
    except ValueError as exc:
        message = str(exc)
        if message == "Tenant suspended":
            logger.error("LOGIN BLOCKED -- Tenant suspended")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=message) from exc
        if message == "Account inactive":
            logger.error("LOGIN FAILED -- inactive account")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc
        logger.error("LOGIN FAILED -- wrong password")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    access_token = issue_login_token(user)
    role = str(user.role).strip().lower()
    features = (
        []
        if role == "super_admin"
        else list_enabled_modules(db, user.tenant_id)
        if role in {"tenant_admin", "client_admin"}
        else list_enabled_member_modules(db, user.tenant_id, user.id)
    )
    logger.info(f'OK LOGIN SUCCESS -- User: "{user.full_name}" (ID: {user.id}) | Role: {build_display_role(user.role)}')
    return AuthResponse(
        token=TokenResponse(access_token=access_token),
        user=UserRead.model_validate(user),
        tenant=tenant,
        features=features,
    )


@router.post("/signup", status_code=status.HTTP_403_FORBIDDEN)
def signup() -> dict[str, str]:
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public signup is disabled.")


def _features_for_user(db: Session, user) -> list[str]:
    role = str(user.role).strip().lower()
    if role == "super_admin":
        return []
    if role in {"tenant_admin", "client_admin"}:
        return list_enabled_modules(db, user.tenant_id)
    return list_enabled_member_modules(db, user.tenant_id, user.id)


@router.get("/me", response_model=UserRead)
def me(current_user = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)


@router.get("/session", response_model=AuthResponse)
def session(
    db: Session = Depends(database_session),
    current_user = Depends(get_current_user),
) -> AuthResponse:
    tenant = None
    if str(current_user.role).strip().lower() != "super_admin":
        tenant = getattr(current_user, "tenant", None)
        if tenant is None:
            tenant = db.query(Tenant).filter_by(id=current_user.tenant_id).one_or_none()
    return AuthResponse(
        token=TokenResponse(access_token=""),
        user=UserRead.model_validate(current_user),
        tenant=tenant,
        features=_features_for_user(db, current_user),
    )


@router.post("/change-password", response_model=UserRead)
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(database_session),
    current_user = Depends(get_current_user),
) -> UserRead:
    logger.info(f'>>> CHANGE PASSWORD -- User: "{current_user.full_name}" (ID: {current_user.id})')
    try:
        updated_user = change_user_password(
            db=db,
            user=current_user,
            current_password=payload.current_password,
            new_password=payload.new_password,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return UserRead.model_validate(updated_user)


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/refresh", response_model=TokenResponse)
def refresh(current_user = Depends(get_current_user)) -> TokenResponse:
    access_token = issue_login_token(current_user)
    return TokenResponse(access_token=access_token)

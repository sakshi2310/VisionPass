"""Tenant admin authentication routes."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session
from app.core.logger import get_logger
from app.core.security import create_access_token
from app.schemas.auth import AuthResponse, LoginRequest, TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_tenant_admin_login, issue_login_token

router = APIRouter()
logger = get_logger("tenant_auth")


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(database_session)) -> AuthResponse:
    logger.info(f'>>> TENANT ADMIN LOGIN ATTEMPT -- email: {payload.email}')
    try:
        tenant, user = authenticate_tenant_admin_login(db, payload.email, payload.password)
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
    logger.info(f'LOGIN SUCCESS -- Tenant Admin: "{user.full_name}" | Tenant: "{tenant.name}"')
    return AuthResponse(
        token=TokenResponse(access_token=access_token, token_type="bearer"),
        user=UserRead.model_validate(user),
        tenant=tenant,
    )

"""Super-admin master feature routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, require_role
from app.schemas.auth import AuthResponse, LoginRequest, TokenResponse
from app.schemas.cv_feature import CvFeatureCreate, CvFeatureListResponse, CvFeatureRead, CvFeatureUpdate
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_super_admin_login, issue_login_token
from app.services.cv_feature_service import (
    create_master_feature,
    delete_master_feature,
    list_master_features,
    update_master_feature,
)

router = APIRouter()


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(database_session)) -> AuthResponse:
    try:
        super_admin = authenticate_super_admin_login(db, payload.email, payload.password)
    except ValueError as exc:
        message = str(exc)
        if message == "Account inactive":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials") from exc

    access_token = issue_login_token(super_admin)
    return AuthResponse(
        token=TokenResponse(access_token=access_token, token_type="bearer"),
        user=UserRead.model_validate(super_admin),
        tenant=None,
    )


@router.get("/features", response_model=CvFeatureListResponse)
def get_features(
    db: Session = Depends(database_session),
    _=Depends(require_role(["SUPER_ADMIN"])),
) -> CvFeatureListResponse:
    return CvFeatureListResponse(features=[CvFeatureRead.model_validate(feature) for feature in list_master_features(db)])


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

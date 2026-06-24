"""User workspace routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_user
from app.models.user import User
from app.schemas.user_workspace import UserWorkspaceDashboardResponse
from app.services.user_workspace_service import get_user_workspace_dashboard

router = APIRouter()


@router.get('/dashboard', response_model=UserWorkspaceDashboardResponse)
def get_dashboard(
    db: Session = Depends(database_session),
    current_user: User = Depends(get_current_tenant_user),
) -> UserWorkspaceDashboardResponse:
    if getattr(current_user, 'role', None) != 'user':
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='User access required')
    return UserWorkspaceDashboardResponse.model_validate(
        get_user_workspace_dashboard(db, current_user.tenant_id, current_user.id)
    )

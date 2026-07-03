"""Client-admin dashboard endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import database_session, get_current_tenant_admin
from app.schemas.dashboard import ClientAdminDashboardSummary, ClientAdminRecentActivity
from app.services.dashboard_service import get_dashboard_summary, get_recent_activity

router = APIRouter()


@router.get("/summary", response_model=ClientAdminDashboardSummary)
def read_dashboard_summary(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> ClientAdminDashboardSummary:
    return ClientAdminDashboardSummary(**get_dashboard_summary(db, current_admin.tenant_id))


@router.get("/recent-activity", response_model=ClientAdminRecentActivity)
def read_recent_activity(
    db: Session = Depends(database_session),
    current_admin=Depends(get_current_tenant_admin),
) -> ClientAdminRecentActivity:
    return ClientAdminRecentActivity(**get_recent_activity(db, current_admin.tenant_id))

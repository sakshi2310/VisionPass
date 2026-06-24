"""Versioned API router aggregation."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    access,
    admin,
    alerts,
    attendance,
    auth,
    cameras,
    employees,
    recognition,
    super_admin,
    tenant_admin,
    tenants,
    tenant_auth,
    tenant_users,
    user_auth,
    user_workspace,
    users,
    visitors,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenant_auth.router, prefix="/tenant/auth", tags=["tenant-auth"])
api_router.include_router(user_auth.router, prefix="/user/auth", tags=["user-auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(super_admin.router, prefix="/super-admin", tags=["super-admin"])
api_router.include_router(tenant_admin.router, prefix="/tenant-admin", tags=["tenant-admin"])
api_router.include_router(user_workspace.router, prefix="/user", tags=["user-workspace"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(tenant_users.router, prefix="/tenant/users", tags=["tenant-users"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(recognition.router, prefix="/recognition", tags=["recognition"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(visitors.router, prefix="/visitors", tags=["visitors"])
api_router.include_router(access.router, prefix="/access", tags=["access"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(cameras.router, prefix="/cameras", tags=["cameras"])

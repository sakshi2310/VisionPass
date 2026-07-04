import { Navigate, Outlet } from "react-router-dom";
import type { ReactElement } from "react";

import { useApp } from "@/context/AppContext";
import type { ModuleKey, Role } from "@/types";
import { dashboardPathForRole } from "@/utils/authRouting";

type ProtectedRouteProps = {
  allowedRoles?: Role[];
  requiredModule?: ModuleKey;
  children?: ReactElement;
};

function isSuperAdmin(role: Role) {
  return role === "SUPER_ADMIN";
}

function accessDeniedMessage(allowedRoles?: Role[], requiredModule?: ModuleKey) {
  if (requiredModule) {
    return "Access denied for this module. Please sign in with the correct account.";
  }
  if (allowedRoles?.includes("SUPER_ADMIN") && allowedRoles.length === 1) {
    return "Super admin access required.";
  }
  if ((allowedRoles?.includes("TENANT_ADMIN") || allowedRoles?.includes("CLIENT_ADMIN")) && allowedRoles.length === 1) {
    return "Tenant admin access required.";
  }
  if (allowedRoles?.includes("TENANT_USER") && allowedRoles.length === 1) {
    return "Tenant user access required.";
  }
  return "Access denied. Please sign in with the correct account.";
}

export function ProtectedRoute({ allowedRoles, requiredModule, children }: ProtectedRouteProps) {
  const { authReady, user, hasModule } = useApp();

  if (!authReady) {
    return (
      <div className="grid min-h-screen place-items-center bg-slate-50 text-slate-700 dark:bg-slate-950 dark:text-slate-200">
        <div className="rounded-3xl border border-slate-200 bg-white px-6 py-4 text-sm shadow-soft backdrop-blur dark:border-white/10 dark:bg-white/5">
          Loading session...
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={dashboardPathForRole(user.role)} replace state={{ message: accessDeniedMessage(allowedRoles, requiredModule) }} />;
  }

  if (requiredModule && !isSuperAdmin(user.role) && !hasModule(requiredModule)) {
    return (
      <div className="grid min-h-[60vh] place-items-center px-4">
        <div className="max-w-md rounded-3xl border border-rose-200 bg-white p-8 text-center shadow-soft dark:border-rose-500/20 dark:bg-white/5">
          <div className="text-sm font-semibold uppercase tracking-[0.24em] text-rose-500">403 · Not Authorized</div>
          <h1 className="mt-3 text-2xl font-semibold">Module not enabled</h1>
          <p className="mt-3 text-sm leading-6 text-slate-500 dark:text-slate-400">
            This feature is not enabled for your tenant. Ask your Super Admin to enable it.
          </p>
        </div>
      </div>
    );
  }

  return children ?? <Outlet />;
}

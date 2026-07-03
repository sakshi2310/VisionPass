import { Navigate, Outlet } from "react-router-dom";
import type { ReactElement } from "react";

import { useApp } from "@/context/AppContext";
import type { ModuleKey, Role } from "@/types";

type ProtectedRouteProps = {
  allowedRoles?: Role[];
  requiredModule?: ModuleKey;
  children?: ReactElement;
};

function isSuperAdmin(role: Role) {
  return role === "SUPER_ADMIN";
}

function loginPathForRoles(allowedRoles?: Role[]) {
  if (allowedRoles?.length === 1 && allowedRoles[0] === "SUPER_ADMIN") return "/admin/login";
  return "/login";
}

function redirectForRole(role: Role) {
  if (isSuperAdmin(role)) return "/admin/login";
  if (role === "CLIENT_ADMIN") return "/client-admin/dashboard";
  return "/login";
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
    return <Navigate to={loginPathForRoles(allowedRoles)} replace state={{ message: accessDeniedMessage(allowedRoles, requiredModule) }} />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={redirectForRole(user.role)} replace state={{ message: accessDeniedMessage(allowedRoles, requiredModule) }} />;
  }

  if (requiredModule && !isSuperAdmin(user.role) && !hasModule(requiredModule)) {
    return <Navigate to={redirectForRole(user.role)} replace state={{ message: accessDeniedMessage(allowedRoles, requiredModule) }} />;
  }

  return children ?? <Outlet />;
}

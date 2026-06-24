import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";

import { AuthLayout } from "@/layouts/AuthLayout";
import { DashboardLayout } from "@/layouts/DashboardLayout";
import { useApp } from "@/context/AppContext";
import { ProtectedRoute } from "@/routes/ProtectedRoute";

const Login = lazy(() => import("@/pages/Login").then((module) => ({ default: module.Login })));
const AdminLogin = lazy(() => import("@/pages/AdminLogin").then((module) => ({ default: module.AdminLogin })));
const Signup = lazy(() => import("@/pages/Signup").then((module) => ({ default: module.Signup })));
const TenantAdminDashboard = lazy(() => import("@/pages/tenant-admin/Dashboard").then((module) => ({ default: module.TenantAdminDashboard })));
const TenantAdminMembers = lazy(() => import("@/pages/tenant-admin/Members").then((module) => ({ default: module.TenantAdminMembers })));
const TenantAdminFeatures = lazy(() => import("@/pages/tenant-admin/Features").then((module) => ({ default: module.TenantAdminFeatures })));
const TenantAdminSettings = lazy(() => import("@/pages/tenant-admin/Settings").then((module) => ({ default: module.TenantAdminSettings })));
const TenantUserDashboard = lazy(() => import("@/pages/user/Dashboard").then((module) => ({ default: module.TenantUserDashboard })));
const TenantUserFeatures = lazy(() => import("@/pages/user/Features").then((module) => ({ default: module.TenantUserFeatures })));
const TenantUserProfile = lazy(() => import("@/pages/user/Profile").then((module) => ({ default: module.TenantUserProfile })));
const AdminDashboard = lazy(() => import("@/pages/admin/AdminDashboard").then((module) => ({ default: module.AdminDashboard })));
const Tenants = lazy(() => import("@/pages/admin/Tenants").then((module) => ({ default: module.Tenants })));
const TenantDetails = lazy(() => import("@/pages/admin/TenantDetails").then((module) => ({ default: module.TenantDetails })));
const Features = lazy(() => import("@/pages/admin/Features").then((module) => ({ default: module.Features })));
const AdminAnalytics = lazy(() => import("@/pages/admin/AdminAnalytics").then((module) => ({ default: module.AdminAnalytics })));
const AuditLogs = lazy(() => import("@/pages/admin/AuditLogs").then((module) => ({ default: module.AuditLogs })));

function HomeRedirect() {
  const { user } = useApp();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role === "SUPER_ADMIN") return <Navigate to="/admin/dashboard" replace />;
  if (user.role === "TENANT_ADMIN") return <Navigate to="/tenant-admin/dashboard" replace />;
  if (user.role === "TENANT_USER") return <Navigate to="/user/dashboard" replace />;
  return <Navigate to="/login" replace />;
}

function DashboardRedirect() {
  return <HomeRedirect />;
}

export function AppRoutes() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center bg-slate-50 text-slate-700 dark:bg-slate-950 dark:text-slate-200">
          <div className="rounded-3xl border border-slate-200 bg-white px-6 py-4 text-sm shadow-soft backdrop-blur dark:border-white/10 dark:bg-white/5">
            Loading VisionPass AI...
          </div>
        </div>
      }
    >
      <Routes>
        <Route element={<AuthLayout />}>
          <Route path="/" element={<Login />} />
          <Route path="/login" element={<Login />} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/bootstrap" element={<Signup />} />
        </Route>

        <Route element={<ProtectedRoute />}>
          <Route element={<DashboardLayout />}>
            <Route path="/dashboard" element={<DashboardRedirect />} />

            <Route element={<ProtectedRoute allowedRoles={["SUPER_ADMIN"]} />}>
              <Route path="/admin/dashboard" element={<AdminDashboard />} />
              <Route path="/admin/tenants" element={<Tenants />} />
              <Route path="/admin/tenants/:tenantId" element={<TenantDetails />} />
              <Route path="/admin/features" element={<Features />} />
              <Route path="/admin/audit-logs" element={<AuditLogs />} />
              <Route path="/admin/analytics" element={<AdminAnalytics />} />
              <Route path="/admin/settings" element={<Navigate to="/admin/dashboard" replace />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["TENANT_ADMIN"]} />}>
              <Route path="/tenant-admin/dashboard" element={<TenantAdminDashboard />} />
              <Route path="/tenant-admin/members" element={<TenantAdminMembers />} />
              <Route path="/tenant-admin/features" element={<TenantAdminFeatures />} />
              <Route path="/tenant-admin/settings" element={<TenantAdminSettings />} />
              <Route path="/tenant-admin/*" element={<Navigate to="/tenant-admin/dashboard" replace />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["TENANT_USER"]} />}>
              <Route path="/user/dashboard" element={<TenantUserDashboard />} />
              <Route path="/user/features" element={<TenantUserFeatures />} />
              <Route path="/user/profile" element={<TenantUserProfile />} />
              <Route path="/user/*" element={<Navigate to="/user/dashboard" replace />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}


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
const AttendanceSettingsPage = lazy(() => import("@/pages/client-admin/attendance/Settings").then((module) => ({ default: module.AttendanceSettingsPage })));
const AttendanceShiftsPage = lazy(() => import("@/pages/client-admin/attendance/Shifts").then((module) => ({ default: module.AttendanceShiftsPage })));
const AttendanceHolidaysPage = lazy(() => import("@/pages/client-admin/attendance/Holidays").then((module) => ({ default: module.AttendanceHolidaysPage })));
const EmployeeListPage = lazy(() => import("@/pages/client-admin/attendance/Employees").then((module) => ({ default: module.EmployeeListPage })));
const EmployeeDetailsPage = lazy(() => import("@/pages/client-admin/attendance/EmployeeDetails").then((module) => ({ default: module.EmployeeDetailsPage })));
const FaceEnrollmentPage = lazy(() => import("@/pages/client-admin/attendance/FaceEnrollment").then((module) => ({ default: module.FaceEnrollmentPage })));
const LiveAttendancePage = lazy(() => import("@/pages/client-admin/attendance/LiveAttendance").then((module) => ({ default: module.LiveAttendancePage })));
const CamerasPage = lazy(() => import("@/pages/client-admin/Cameras").then((module) => ({ default: module.CamerasPage })));
const LiveRecognitionPage = lazy(() => import("@/pages/client-admin/LiveRecognition").then((module) => ({ default: module.LiveRecognitionPage })));
const ClientAdminDashboard = lazy(() => import("@/pages/client-admin/Dashboard").then((module) => ({ default: module.ClientAdminDashboard })));
const ReportsPage = lazy(() => import("@/pages/client-admin/Reports").then((module) => ({ default: module.ReportsPage })));
const Visitors = lazy(() => import("@/pages/client/Visitors").then((module) => ({ default: module.Visitors })));
const AccessControl = lazy(() => import("@/pages/client/AccessControl").then((module) => ({ default: module.AccessControl })));
const Alerts = lazy(() => import("@/pages/client/Alerts").then((module) => ({ default: module.Alerts })));
const TenantUserDashboard = lazy(() => import("@/pages/user/Dashboard").then((module) => ({ default: module.TenantUserDashboard })));
const TenantUserProfile = lazy(() => import("@/pages/user/Profile").then((module) => ({ default: module.TenantUserProfile })));
const TenantUserAttendance = lazy(() => import("@/pages/user/Attendance").then((module) => ({ default: module.TenantUserAttendance })));
const TenantUserNotifications = lazy(() => import("@/pages/user/Notifications").then((module) => ({ default: module.TenantUserNotifications })));
const TenantUserSettings = lazy(() => import("@/pages/user/Settings").then((module) => ({ default: module.TenantUserSettings })));
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
  if (user.role === "CLIENT_ADMIN") return <Navigate to="/client-admin/dashboard" replace />;
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
            Loading Vision Pass...
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

            <Route element={<ProtectedRoute allowedRoles={["TENANT_ADMIN", "CLIENT_ADMIN"]} />}>
              <Route path="/tenant-admin/dashboard" element={<TenantAdminDashboard />} />
              <Route path="/tenant-admin/members" element={<TenantAdminMembers />} />
              <Route path="/tenant-admin/features" element={<TenantAdminFeatures />} />
              <Route path="/tenant-admin/settings" element={<TenantAdminSettings />} />

              <Route path="/client-admin/dashboard" element={<ClientAdminDashboard />} />
              <Route path="/client-admin/members" element={<TenantAdminMembers />} />
              <Route path="/client-admin/features" element={<TenantAdminFeatures />} />
              <Route path="/client-admin/settings" element={<TenantAdminSettings />} />
              <Route path="/client-admin/attendance/settings" element={<AttendanceSettingsPage />} />
              <Route path="/client-admin/attendance/shifts" element={<AttendanceShiftsPage />} />
              <Route path="/client-admin/attendance/holidays" element={<AttendanceHolidaysPage />} />
              <Route path="/client-admin/attendance/employees" element={<EmployeeListPage />} />
              <Route path="/client-admin/attendance/employees/:id" element={<EmployeeDetailsPage />} />
              <Route path="/client-admin/attendance/face-enrollment" element={<FaceEnrollmentPage />} />
              <Route path="/client-admin/attendance/live" element={<LiveAttendancePage />} />
              <Route path="/client-admin/cameras" element={<CamerasPage />} />
              <Route path="/client-admin/cameras/live" element={<LiveRecognitionPage />} />
              <Route path="/client-admin/visitors" element={<Visitors />} />
              <Route path="/client-admin/access-control" element={<AccessControl />} />
              <Route path="/client-admin/alerts" element={<Alerts />} />
              <Route path="/client-admin/reports" element={<ReportsPage />} />

              <Route path="/tenant-admin/*" element={<Navigate to="/tenant-admin/dashboard" replace />} />
              <Route path="/client-admin/*" element={<Navigate to="/client-admin/dashboard" replace />} />
            </Route>

            <Route element={<ProtectedRoute allowedRoles={["TENANT_USER"]} />}>
              <Route path="/user/dashboard" element={<TenantUserDashboard />} />
              <Route path="/user/attendance" element={<TenantUserAttendance />} />
              <Route path="/user/profile" element={<TenantUserProfile />} />
              <Route path="/user/notifications" element={<TenantUserNotifications />} />
              <Route path="/user/settings" element={<TenantUserSettings />} />
              <Route path="/user/*" element={<Navigate to="/user/dashboard" replace />} />
            </Route>
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

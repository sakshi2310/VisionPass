import type { ModuleDefinition, NavItem } from "@/types";

export const moduleDefinitions: ModuleDefinition[] = [
  {
    key: "attendance",
    label: "Attendance",
    description: "Daily check-ins and attendance logs.",
    route: "/dashboard/attendance",
    icon: "CalendarCheck2",
  },
  {
    key: "visitor_classification",
    label: "Visitors",
    description: "Unknown and staff classification logs.",
    route: "/dashboard/visitors",
    icon: "ScanFace",
  },
];

export const clientNavItems: NavItem[] = [
  { key: "dashboard", label: "Dashboard", path: "/dashboard", icon: "LayoutDashboard" },
  {
    key: "attendance",
    label: "Attendance",
    path: "/dashboard/attendance",
    icon: "CalendarCheck2",
    moduleKey: "attendance",
  },
  {
    key: "visitors",
    label: "Visitors",
    path: "/dashboard/visitors",
    icon: "ScanFace",
    moduleKey: "visitor_classification",
  },
  {
    key: "users",
    label: "Users",
    path: "/dashboard/users",
    icon: "Users",
    adminOnly: true,
  },
  { key: "settings", label: "Settings", path: "/dashboard/settings", icon: "Settings2" },
];

export const tenantAdminNavItems: NavItem[] = [
  { key: "tenant-dashboard", label: "Dashboard", path: "/tenant-admin/dashboard", icon: "LayoutDashboard" },
  { key: "tenant-members", label: "Members", path: "/tenant-admin/members", icon: "Users" },
  { key: "tenant-features", label: "Features", path: "/tenant-admin/features", icon: "Sparkles" },
  { key: "tenant-settings", label: "Settings", path: "/tenant-admin/settings", icon: "Settings2" },
];

export const tenantMemberNavItems: NavItem[] = [
  { key: "user-dashboard", label: "Dashboard", path: "/user/dashboard", icon: "LayoutDashboard" },
  { key: "user-features", label: "My Features", path: "/user/features", icon: "Sparkles" },
  { key: "user-profile", label: "Profile", path: "/user/profile", icon: "Users" },
];

export const tenantUserNavItems: NavItem[] = [
  { key: "user-dashboard", label: "Dashboard", path: "/user/dashboard", icon: "LayoutDashboard" },
  { key: "user-security", label: "Security", path: "/user/security", icon: "ShieldCheck" },
  { key: "user-reception", label: "Reception", path: "/user/reception", icon: "Building2" },
  { key: "user-attendance", label: "Attendance", path: "/user/attendance", icon: "CalendarCheck2" },
  { key: "user-cameras", label: "Cameras", path: "/user/cameras", icon: "DoorOpen" },
  { key: "user-settings", label: "Settings", path: "/user/settings", icon: "Settings2" },
];

export const clientUserNavKeys = new Set([
  "dashboard",
  "attendance",
  "visitors",
]);

export const adminNavItems: NavItem[] = [
  { key: 'admin-dashboard', label: 'Dashboard', path: '/admin/dashboard', icon: 'LayoutDashboard' },
  { key: 'admin-tenants', label: 'Tenants', path: '/admin/tenants', icon: 'Building2' },
  { key: 'admin-features', label: 'Features', path: '/admin/features', icon: 'SlidersHorizontal' },
  { key: 'admin-audit-logs', label: 'Audit Logs', path: '/admin/audit-logs', icon: 'ClipboardList' },
  {
    key: 'admin-analytics',
    label: 'Platform Analytics',
    path: '/admin/analytics',
    icon: 'ChartColumnIncreasing',
  },
  { key: 'settings', label: 'Settings', path: '/admin/settings', icon: 'Settings2' },
];

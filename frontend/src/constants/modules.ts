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
    key: "visitor_unknown",
    label: "Visitor + Unknown",
    description: "Person detection, visitors, unknown review, and reports.",
    route: "/client-admin/visitor-unknown/person-detection",
    icon: "ScanFace",
  },
  {
    key: "object_detection",
    label: "Object Detection",
    description: "Detect configured objects in live video.",
    route: "/client-admin/object-detection",
    icon: "ScanFace",
  },
];

const attendanceNavGroup: NavItem = {
  key: "tenant-attendance",
  label: "Attendance",
  path: "/client-admin/attendance/members",
  icon: "CalendarCheck2",
  moduleKey: "attendance",
  children: [
    { key: "tenant-attendance-members", label: "Members", path: "/client-admin/attendance/members", icon: "Users" },
    { key: "tenant-attendance-board", label: "Attendance Board", path: "/client-admin/attendance/board", icon: "ClipboardList" },
    { key: "tenant-attendance-live", label: "Live Attendance", path: "/client-admin/attendance/live", icon: "ScanFace" },
    { key: "tenant-attendance-reports", label: "Attendance Reports", path: "/client-admin/reports", icon: "ChartColumnIncreasing" },
  ],
};

const objectDetectionNavGroup: NavItem = {
  key: "tenant-object-detection",
  label: "Object Detection",
  path: "/client-admin/object-detection",
  icon: "ScanFace",
  moduleKey: "object_detection",
  children: [
    { key: "tenant-detection-live", label: "Live Monitoring", path: "/client-admin/object-detection/live", icon: "ScanFace" },
    { key: "tenant-detection-events", label: "Detection Events", path: "/client-admin/object-detection/events", icon: "ClipboardList" },
    { key: "tenant-detection-models", label: "Models & Classes", path: "/client-admin/object-detection/models", icon: "SlidersHorizontal" },
    { key: "tenant-detection-rules", label: "Detection Rules", path: "/client-admin/object-detection/rules", icon: "ShieldCheck" },
    { key: "tenant-detection-alerts", label: "Detection Alerts", path: "/client-admin/object-detection/alerts", icon: "Bell" },
    { key: "tenant-detection-reports", label: "Detection Reports", path: "/client-admin/object-detection/reports", icon: "ChartColumnIncreasing" },
  ],
};

const visitorUnknownNavGroup: NavItem = {
  key: "tenant-visitor-unknown",
  label: "Visitor + Unknown",
  path: "/client-admin/visitor-unknown/person-detection",
  icon: "ScanFace",
  moduleKey: "visitor_unknown",
  children: [
    { key: "tenant-visitor-unknown-person-detection", label: "Person Detection", path: "/client-admin/visitor-unknown/person-detection", icon: "ScanFace" },
    { key: "tenant-visitor-unknown-visitors", label: "Visitors", path: "/client-admin/visitor-unknown/visitors", icon: "Users" },
    { key: "tenant-visitor-unknown-review", label: "Unknown Review", path: "/client-admin/visitor-unknown/unknown-review", icon: "Search" },
    { key: "tenant-visitor-unknown-reports", label: "Reports", path: "/client-admin/visitor-unknown/reports", icon: "ChartColumnIncreasing" },
  ],
};

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
    label: "Visitor + Unknown",
    path: "/dashboard/visitor-unknown/person-detection",
    icon: "ScanFace",
    moduleKey: "visitor_unknown",
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
  {
    key: "tenant-cameras",
    label: "Camera Management",
    path: "/tenant-admin/cameras",
    icon: "DoorOpen",
    children: [
      { key: "tenant-cameras-config", label: "Camera Sources", path: "/tenant-admin/cameras", icon: "DoorOpen" },
      { key: "tenant-cameras-zones", label: "Zone View", path: "/tenant-admin/cameras/zones", icon: "ScanFace" },
    ],
  },
  { key: "tenant-staff", label: "Staff", path: "/client-admin/staff", icon: "Users" },
  { key: "tenant-portal-users", label: "Portal Users", path: "/tenant-admin/portal-users", icon: "Users" },
  visitorUnknownNavGroup,
  attendanceNavGroup,
  objectDetectionNavGroup,
  { key: "tenant-access", label: "Access Logs", path: "/client-admin/access-control", icon: "ShieldCheck", moduleKey: "access_control" },
  { key: "tenant-alerts", label: "Alerts", path: "/client-admin/alerts", icon: "ClipboardList", moduleKey: "alerts" },
  { key: "tenant-reports", label: "Reports Overview", path: "/client-admin/reports", icon: "ChartColumnIncreasing" },
  { key: "tenant-features", label: "Features", path: "/tenant-admin/features", icon: "Sparkles" },
  { key: "tenant-settings", label: "Settings", path: "/tenant-admin/settings", icon: "Settings2" },
];

export const tenantMemberNavItems: NavItem[] = [
  { key: "user-dashboard", label: "Dashboard", path: "/user/dashboard", icon: "LayoutDashboard" },
  { key: "user-attendance", label: "My Attendance", path: "/user/attendance", icon: "CalendarCheck2", moduleKey: "attendance" },
  { key: "user-profile", label: "My Profile", path: "/user/profile", icon: "UserRound" },
  { key: "user-notifications", label: "Notifications", path: "/user/notifications", icon: "Bell" },
  { key: "user-settings", label: "Settings", path: "/user/settings", icon: "Settings2" },
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

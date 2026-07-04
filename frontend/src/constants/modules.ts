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

const attendanceNavGroup: NavItem = {
  key: "tenant-attendance",
  label: "Attendance",
  path: "/client-admin/attendance/settings",
  icon: "CalendarCheck2",
  moduleKey: "attendance",
  children: [
    { key: "tenant-attendance-live", label: "Live Attendance", path: "/client-admin/attendance/live", icon: "ScanFace" },
    { key: "tenant-attendance-settings", label: "Attendance Settings", path: "/client-admin/attendance/settings", icon: "Settings2" },
    { key: "tenant-attendance-shifts", label: "Shift Management", path: "/client-admin/attendance/shifts", icon: "CalendarCheck2" },
    { key: "tenant-attendance-holidays", label: "Holiday Management", path: "/client-admin/attendance/holidays", icon: "ClipboardList" },
    { key: "tenant-attendance-employees", label: "Employees", path: "/client-admin/attendance/employees", icon: "Users" },
    { key: "tenant-attendance-face-enrollment", label: "Face Enrollment", path: "/client-admin/attendance/face-enrollment", icon: "ScanFace" },
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
    { key: "tenant-detection-zones", label: "Zones & Confidence", path: "/client-admin/object-detection/zones", icon: "Settings2" },
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
  attendanceNavGroup,
  objectDetectionNavGroup,
  { key: "tenant-visitors", label: "Visitors", path: "/client-admin/visitors", icon: "Users", moduleKey: "visitor_management" },
  { key: "tenant-access", label: "Access Logs", path: "/client-admin/access-control", icon: "ShieldCheck", moduleKey: "access_control" },
  { key: "tenant-alerts", label: "Alerts", path: "/client-admin/alerts", icon: "ClipboardList", moduleKey: "alerts" },
  { key: "tenant-reports", label: "Reports Overview", path: "/client-admin/reports", icon: "ChartColumnIncreasing" },
  {
    key: "tenant-cameras",
    label: "Camera Management",
    path: "/client-admin/cameras",
    icon: "DoorOpen",
    moduleKey: "camera_management",
    children: [
      { key: "tenant-camera-management", label: "Camera Management", path: "/client-admin/cameras", icon: "DoorOpen" },
      { key: "tenant-live-recognition", label: "Live Recognition", path: "/client-admin/cameras/live", icon: "ScanFace" },
    ],
  },
  { key: "tenant-members", label: "Members", path: "/tenant-admin/members", icon: "Users" },
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

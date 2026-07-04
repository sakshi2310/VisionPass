import type { Role } from "@/types";

export function dashboardPathForRole(role: Role | string): string {
  switch (role.toUpperCase()) {
    case "SUPER_ADMIN":
      return "/admin/dashboard";
    case "TENANT_ADMIN":
      return "/tenant-admin/dashboard";
    case "CLIENT_ADMIN":
      return "/client-admin/dashboard";
    case "TENANT_USER":
    case "USER":
    case "CLIENT_USER":
    case "SECURITY_GUARD":
    case "RECEPTIONIST":
    case "ATTENDANCE_OPERATOR":
    case "CAMERA_OPERATOR":
    case "MANAGER":
      return "/user/dashboard";
    default:
      return "/login";
  }
}

import type { Role, Tenant, User } from "@/types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const TOKEN_KEY = "visionpass-token";
const USER_KEY = "visionpass-user";

export type TenantAuthSession = {
  token: string;
  user: User;
  tenant: Tenant | null;
  features: string[];
};

type ApiUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string | null;
  phone?: string | null;
  department?: string | null;
  designation?: string | null;
  employee_id?: string | null;
  access_zones?: string[] | null;
  face_enrolled?: boolean;
  is_active?: boolean;
  is_deleted?: boolean;
  notes?: string | null;
  last_login_at?: string | null;
  created_by?: string | null;
};

type ApiTenant = {
  id: string;
  name: string;
  slug: string;
  industry: string;
  plan: string;
  status: string;
};

type ApiAuthResponse = {
  token: {
    access_token: string;
    token_type: string;
  };
  user: ApiUser;
  tenant?: ApiTenant | null;
  features?: string[];
};

function hasWindow() {
  return typeof window !== "undefined";
}

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : "/" + path;
  if (!API_BASE) return normalizedPath;
  if (API_BASE.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return API_BASE + normalizedPath.slice(4);
  }
  return API_BASE + normalizedPath;
}

function normalizeRole(role: string): Role {
  const canonical = role.toUpperCase();
  if (
    canonical === "SUPER_ADMIN" ||
    canonical === "TENANT_ADMIN" ||
    canonical === "TENANT_USER" ||
    canonical === "SECURITY_GUARD" ||
    canonical === "RECEPTIONIST" ||
    canonical === "ATTENDANCE_OPERATOR" ||
    canonical === "CAMERA_OPERATOR" ||
    canonical === "MANAGER" ||
    canonical === "CLIENT_ADMIN" ||
    canonical === "CLIENT_USER"
  ) {
    return canonical;
  }
  return "TENANT_USER";
}

function buildTitle(role: Role) {
  switch (role) {
    case "SUPER_ADMIN":
      return "Platform Super Admin";
    case "TENANT_ADMIN":
    case "CLIENT_ADMIN":
      return "Tenant Admin";
    case "SECURITY_GUARD":
      return "Security Guard";
    case "RECEPTIONIST":
      return "Receptionist";
    case "ATTENDANCE_OPERATOR":
      return "Attendance Operator";
    case "CAMERA_OPERATOR":
      return "Camera Operator";
    case "MANAGER":
      return "Manager";
    case "TENANT_USER":
    case "CLIENT_USER":
    default:
      return "Tenant User";
  }
}

function normalizeUser(user: ApiUser): User {
  const role = normalizeRole(user.role);
  return {
    id: user.id,
    name: user.full_name,
    email: user.email,
    role,
    tenantId: user.tenant_id ?? "",
    title: buildTitle(role),
    phone: user.phone ?? undefined,
    department: user.department ?? undefined,
    designation: user.designation ?? undefined,
    employeeId: user.employee_id ?? undefined,
    accessZones: user.access_zones ?? undefined,
    faceEnrolled: user.face_enrolled ?? undefined,
    isActive: user.is_active ?? undefined,
    isDeleted: user.is_deleted ?? undefined,
    notes: user.notes ?? undefined,
    lastLoginAt: user.last_login_at ?? undefined,
    createdBy: user.created_by ?? undefined,
  };
}

function normalizeTenant(tenant: ApiTenant | null | undefined): Tenant | null {
  if (!tenant) return null;
  return {
    id: tenant.id,
    name: tenant.name,
    code: tenant.slug.toUpperCase().replace(/[^A-Z0-9]+/g, "-").slice(0, 12),
    plan: tenant.plan,
    industry: tenant.industry,
    status: tenant.status as Tenant["status"],
    enabledModules: [],
    users: 0,
    sites: tenant.status === "active" ? 1 : 0,
    alertsToday: 0,
    cameras: 0,
  };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed.";
    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Keep the default message.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

function saveStoredAccessToken(token: string | null) {
  if (!hasWindow()) return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function saveStoredUser(user: User | null) {
  if (!hasWindow()) return;
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

export async function loginTenantAdmin(email: string, password: string): Promise<TenantAuthSession> {
  const session = await requestJson<ApiAuthResponse>("/api/tenant/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  const user = normalizeUser(session.user);
  const tenant = normalizeTenant(session.tenant);
  saveStoredAccessToken(session.token.access_token);
  saveStoredUser(user);
  return {
    token: session.token.access_token,
    user,
    tenant,
    features: session.features ?? [],
  };
}

export async function loginTenantUser(email: string, password: string): Promise<TenantAuthSession> {
  const session = await requestJson<ApiAuthResponse>("/api/user/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  const user = normalizeUser(session.user);
  const tenant = normalizeTenant(session.tenant);
  saveStoredAccessToken(session.token.access_token);
  saveStoredUser(user);
  return {
    token: session.token.access_token,
    user,
    tenant,
    features: session.features ?? [],
  };
}

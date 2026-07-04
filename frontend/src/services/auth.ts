import type { Role, User } from "@/types";

const USER_KEY = "visionpass-user";
const TOKEN_KEY = "visionpass-token";
const TENANT_KEY = "visionpass-current-tenant";
const THEME_KEY = "visionpass-theme";
const TENANTS_KEY = "visionpass-tenants";
const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type AuthSession = {
  token: string;
  user: User;
  tenant: ReturnType<typeof normalizeTenant>;
};

type ApiUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string | null;
  is_active: boolean;
  created_at: string;
};

type ApiAuthResponse = {
  access_token?: string;
  token_type?: string;
  token: {
    access_token: string;
    token_type: string;
  };
  user: ApiUser;
  features?: string[];
  tenant?: {
    id: string;
    name: string;
    slug: string;
    industry: string;
    plan: string;
    status: string;
  } | null;
};

type BootstrapStatusResponse = {
  setup_required: boolean;
};

function hasWindow() {
  return typeof window !== "undefined";
}

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  if (!API_BASE) return normalizedPath;
  if (API_BASE.endsWith("/api") && normalizedPath.startsWith("/api/")) {
    return `${API_BASE}${normalizedPath.slice(4)}`;
  }
  return `${API_BASE}${normalizedPath}`;
}

function authHeaders(token?: string) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }
  return headers;
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
    default:
      return "Tenant User";
  }
}

function normalizeUser(user: ApiUser | User): User {
  if ("tenantId" in user) {
    const role = normalizeRole(user.role);
    return {
      ...user,
      role,
      title: user.title ?? buildTitle(role),
    };
  }

  const role = normalizeRole(user.role);
  return {
    id: user.id,
    name: user.full_name,
    email: user.email,
    role,
    tenantId: user.tenant_id ?? "",
    title: buildTitle(role),
  };
}

function normalizeTenant(
  tenant:
    | {
        id: string;
        name: string;
        slug: string;
        industry: string;
        plan: string;
        status: string;
        company_email?: string | null;
        logo_url?: string | null;
        address?: string | null;
      }
    | null
    | undefined,
  enabledModules: string[] = [],
) {
  if (!tenant) return null;
  return {
    id: tenant.id,
    name: tenant.name,
    code: tenant.slug.toUpperCase().replace(/[^A-Z0-9]+/g, "-").slice(0, 12),
    plan: tenant.plan,
    industry: tenant.industry,
    status: tenant.status as "active" | "trial" | "paused",
    enabledModules,
    users: 0,
    sites: tenant.status === "active" ? 1 : 0,
    alertsToday: 0,
    cameras: 0,
    companyEmail: tenant.company_email ?? undefined,
    logo_url: tenant.logo_url ?? undefined,
    address: tenant.address ?? undefined,
  };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = "Request failed.";
    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Keep default message.
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export function loadStoredUser() {
  if (!hasWindow()) return null;
  const raw = localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as User) : null;
}

export function saveStoredUser(user: User | null) {
  if (!hasWindow()) return;
  if (user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(USER_KEY);
  }
}

export function loadStoredAccessToken() {
  if (!hasWindow()) return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function saveStoredAccessToken(token: string | null) {
  if (!hasWindow()) return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

export function loadStoredTenantId() {
  if (!hasWindow()) return null;
  return localStorage.getItem(TENANT_KEY);
}

export function saveStoredTenantId(tenantId: string | null) {
  if (!hasWindow()) return;
  if (tenantId) {
    localStorage.setItem(TENANT_KEY, tenantId);
  } else {
    localStorage.removeItem(TENANT_KEY);
  }
}

export function loadStoredTheme() {
  if (!hasWindow()) return "dark" as const;
  return (localStorage.getItem(THEME_KEY) as "dark" | "light" | null) ?? "dark";
}

export function saveStoredTheme(theme: "dark" | "light") {
  if (!hasWindow()) return;
  localStorage.setItem(THEME_KEY, theme);
}

export function loadStoredTenants<T>(fallback: T) {
  if (!hasWindow()) return fallback;
  const raw = localStorage.getItem(TENANTS_KEY);
  return raw ? (JSON.parse(raw) as T) : fallback;
}

export function saveStoredTenants<T>(tenants: T) {
  if (!hasWindow()) return;
  localStorage.setItem(TENANTS_KEY, JSON.stringify(tenants));
}

export function clearSession() {
  saveStoredUser(null);
  saveStoredAccessToken(null);
  saveStoredTenantId(null);
}

export async function login(email: string, password: string): Promise<AuthSession> {
  const session = await requestJson<ApiAuthResponse>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  const user = normalizeUser(session.user);
  const tenant = normalizeTenant(session.tenant, session.features ?? []);
  const accessToken = session.access_token ?? session.token.access_token;
  saveStoredAccessToken(accessToken);
  saveStoredUser(user);
  return {
    token: accessToken,
    user,
    tenant,
  };
}

export async function checkBootstrapStatus(): Promise<boolean> {
  const response = await requestJson<BootstrapStatusResponse>("/api/auth/bootstrap-status");
  return response.setup_required;
}

export async function bootstrapSuperAdmin(
  fullName: string,
  email: string,
  password: string,
  organizationName = "VisionPass Platform",
): Promise<AuthSession> {
  const session = await requestJson<ApiAuthResponse>("/api/auth/bootstrap", {
    method: "POST",
    body: JSON.stringify({
      full_name: fullName,
      email,
      password,
      organization_name: organizationName,
    }),
  });
  const user = normalizeUser(session.user);
  const tenant = normalizeTenant(session.tenant);
  saveStoredAccessToken(session.token.access_token);
  saveStoredUser(user);
  return {
    token: session.token.access_token,
    user,
    tenant,
  };
}

export async function signup(
  fullName: string,
  email: string,
  organizationName: string,
  password: string,
): Promise<AuthSession> {
  const session = await requestJson<ApiAuthResponse>("/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({
      full_name: fullName,
      email,
      organization_name: organizationName,
      password,
    }),
  });
  const user = normalizeUser(session.user);
  const tenant = normalizeTenant(session.tenant);
  saveStoredAccessToken(session.token.access_token);
  saveStoredUser(user);
  return {
    token: session.token.access_token,
    user,
    tenant,
  };
}

export async function changePassword(currentPassword: string, newPassword: string) {
  const token = loadStoredAccessToken();
  if (!token) {
    throw new Error("You must be signed in.");
  }

  const updatedUser = await requestJson<ApiUser>("/api/auth/change-password", {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });

  const normalized = normalizeUser(updatedUser);
  saveStoredUser(normalized);
  return normalized;
}

export async function logout() {
  const token = loadStoredAccessToken();
  if (token) {
    try {
      await fetch(buildApiUrl("/api/auth/logout"), {
        method: "POST",
        headers: authHeaders(token),
      });
    } catch {
      // Ignore logout failures and still clear local session state.
    }
  }
  clearSession();
}

export async function getCurrentSession(): Promise<AuthSession | null> {
  const token = loadStoredAccessToken();
  if (!token) return null;

  try {
    const session = await requestJson<ApiAuthResponse>("/api/auth/session", {
      headers: authHeaders(token),
    });
    const user = normalizeUser(session.user);
    const tenant = normalizeTenant(session.tenant, session.features ?? []);
    saveStoredUser(user);
    return {
      token,
      user,
      tenant,
    };
  } catch {
    clearSession();
    return null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  const session = await getCurrentSession();
  return session?.user ?? null;
}

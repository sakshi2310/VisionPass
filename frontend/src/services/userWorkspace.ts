import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");
const USER_MODULES_KEY = "visionpass-user-modules";

export type UserWorkspaceFeature = {
  feature_name: string;
  feature_code: string;
  description?: string | null;
  module_key?: string | null;
  route?: string | null;
};

export type UserWorkspaceProfile = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
  tenant_id: string;
  phone?: string | null;
  department?: string | null;
  designation?: string | null;
  employee_id?: string | null;
  last_login_at?: string | null;
  created_at: string;
};

export type UserWorkspaceSummary = {
  tenant_name: string;
  member_name: string;
  member_role: string;
  tenant_id: string;
  member_id: string;
  profile_status: string;
  assigned_features_count: number;
  open_modules_count: number;
};

export type UserWorkspaceDashboard = {
  summary: UserWorkspaceSummary;
  profile: UserWorkspaceProfile | null;
  features: UserWorkspaceFeature[];
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

function authHeaders() {
  const token = loadStoredAccessToken();
  return token ? { Authorization: "Bearer " + token } : {};
}

function saveStoredModuleKeys(moduleKeys: string[]) {
  if (!hasWindow()) return;
  localStorage.setItem(USER_MODULES_KEY, JSON.stringify(moduleKeys));
}

export function loadStoredUserModuleKeys() {
  if (!hasWindow()) return [] as string[];
  const raw = localStorage.getItem(USER_MODULES_KEY);
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.filter((value): value is string => typeof value === "string") : [];
  } catch {
    return [];
  }
}

export function clearStoredUserModuleKeys() {
  if (!hasWindow()) return;
  localStorage.removeItem(USER_MODULES_KEY);
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
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
      // keep default
    }
    throw new Error(message);
  }

  return (await response.json()) as T;
}

export async function getUserWorkspaceDashboard(): Promise<UserWorkspaceDashboard> {
  const dashboard = await requestJson<UserWorkspaceDashboard>("/api/user/dashboard");
  saveStoredModuleKeys(dashboard.features.map((feature) => feature.module_key ?? feature.feature_code));
  return dashboard;
}

import type { Role } from "@/types";
import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type TenantUserRecord = {
  id: string;
  email: string;
  name: string;
  fullName: string;
  role: Role;
  tenantId: string;
  phone?: string | null;
  department?: string | null;
  designation?: string | null;
  employeeId?: string | null;
  accessZones: string[];
  faceEnrolled: boolean;
  isActive: boolean;
  isDeleted: boolean;
  notes?: string | null;
  lastLoginAt?: string | null;
  createdBy?: string | null;
  createdAt: string;
  updatedAt: string;
};

type RawTenantUser = {
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
  created_at: string;
  updated_at: string;
};

type RawListResponse = { users: RawTenantUser[] };

type TenantUserPayload = {
  full_name: string;
  email: string;
  password: string;
  phone?: string | null;
  role: string;
  department?: string | null;
  designation?: string | null;
  employee_id?: string | null;
  access_zones?: string[];
  is_active?: boolean;
  face_enrolled?: boolean;
  notes?: string | null;
};

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

function normalizeUser(raw: RawTenantUser): TenantUserRecord {
  return {
    id: raw.id,
    email: raw.email,
    name: raw.full_name,
    fullName: raw.full_name,
    role: raw.role.toUpperCase() as Role,
    tenantId: raw.tenant_id ?? "",
    phone: raw.phone ?? null,
    department: raw.department ?? null,
    designation: raw.designation ?? null,
    employeeId: raw.employee_id ?? null,
    accessZones: raw.access_zones ?? [],
    faceEnrolled: raw.face_enrolled ?? false,
    isActive: raw.is_active ?? true,
    isDeleted: raw.is_deleted ?? false,
    notes: raw.notes ?? null,
    lastLoginAt: raw.last_login_at ?? null,
    createdBy: raw.created_by ?? null,
    createdAt: raw.created_at,
    updatedAt: raw.updated_at,
  };
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
      // Keep the default message.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const tenantUsersApi = {
  list: async () => {
    const response = await requestJson<RawListResponse>("/api/tenant/users");
    return response.users.map(normalizeUser);
  },
  create: (payload: TenantUserPayload) =>
    requestJson<RawTenantUser>("/api/tenant/users/create", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then(normalizeUser),
  get: (userId: string) => requestJson<RawTenantUser>("/api/tenant/users/" + userId).then(normalizeUser),
  update: (userId: string, payload: Partial<TenantUserPayload>) =>
    requestJson<RawTenantUser>("/api/tenant/users/" + userId, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }).then(normalizeUser),
  updateStatus: (userId: string, payload: Pick<TenantUserPayload, "is_active" | "face_enrolled">) =>
    requestJson<RawTenantUser>("/api/tenant/users/" + userId + "/status", {
      method: "PATCH",
      body: JSON.stringify(payload),
    }).then(normalizeUser),
  remove: (userId: string) =>
    requestJson<void>("/api/tenant/users/" + userId, {
      method: "DELETE",
    }),
};
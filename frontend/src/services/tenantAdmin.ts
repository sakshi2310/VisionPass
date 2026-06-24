import type { Role } from "@/types";
import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type TenantAdminDashboardSummary = {
  total_members: number;
  tenant_admins: number;
  users: number;
  enabled_features: number;
};

export type TenantAdminFeature = {
  feature_name: string;
  feature_code: string;
  description?: string | null;
};

type RawTenantAdminMember = {
  id: string;
  full_name: string;
  email: string;
  role: string;
  status: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TenantAdminMember = {
  id: string;
  full_name: string;
  email: string;
  role: Role;
  status: "active" | "inactive" | "suspended";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

type TenantAdminMemberListResponse = { members: RawTenantAdminMember[] };
type TenantAdminFeatureListResponse = { features: TenantAdminFeature[] };
type TenantAdminMemberFeatureCodesResponse = { feature_codes: string[] };

export type TenantAdminMemberPayload = {
  full_name: string;
  email: string;
  password: string;
  role: "tenant_admin" | "user";
  status: "active" | "inactive" | "suspended";
  feature_codes?: string[];
};

type TenantAdminMemberUpdatePayload = Partial<TenantAdminMemberPayload>;

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

function normalizeRole(role: string): Role {
  const value = role.toUpperCase();
  if (
    value === "SUPER_ADMIN" ||
    value === "TENANT_ADMIN" ||
    value === "TENANT_USER" ||
    value === "SECURITY_GUARD" ||
    value === "RECEPTIONIST" ||
    value === "ATTENDANCE_OPERATOR" ||
    value === "CAMERA_OPERATOR" ||
    value === "MANAGER" ||
    value === "CLIENT_ADMIN" ||
    value === "CLIENT_USER"
  ) {
    return value;
  }
  return "TENANT_USER";
}

function normalizeStatus(status: string): TenantAdminMember["status"] {
  if (status === "inactive" || status === "suspended") return status;
  return "active";
}

function normalizeMember(member: RawTenantAdminMember): TenantAdminMember {
  return {
    id: member.id,
    full_name: member.full_name,
    email: member.email,
    role: normalizeRole(member.role),
    status: normalizeStatus(member.status),
    is_active: member.is_active,
    created_at: member.created_at,
    updated_at: member.updated_at,
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
      // keep default message
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const tenantAdminApi = {
  getDashboardSummary: () => requestJson<TenantAdminDashboardSummary>("/api/tenant-admin/dashboard"),
  listMembers: async () => {
    const response = await requestJson<TenantAdminMemberListResponse>("/api/tenant-admin/members");
    return response.members.map(normalizeMember);
  },
  createMember: (payload: TenantAdminMemberPayload) =>
    requestJson<RawTenantAdminMember>("/api/tenant-admin/members", {
      method: "POST",
      body: JSON.stringify(payload),
    }).then(normalizeMember),
  updateMember: (memberId: string, payload: TenantAdminMemberUpdatePayload) =>
    requestJson<RawTenantAdminMember>("/api/tenant-admin/members/" + memberId, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }).then(normalizeMember),
  deleteMember: (memberId: string) =>
    requestJson<void>("/api/tenant-admin/members/" + memberId, {
      method: "DELETE",
    }),
  listFeatures: async () => {
    const response = await requestJson<TenantAdminFeatureListResponse>("/api/tenant-admin/features");
    return response.features;
  },
  listMemberFeatures: async (memberId: string) => {
    const response = await requestJson<TenantAdminMemberFeatureCodesResponse>(`/api/tenant-admin/members/${memberId}/features`);
    return response.feature_codes;
  },
  updateMemberFeatures: (memberId: string, featureCodes: string[]) =>
    requestJson<TenantAdminMemberFeatureCodesResponse>(`/api/tenant-admin/members/${memberId}/features`, {
      method: "PUT",
      body: JSON.stringify({ feature_codes: featureCodes }),
    }),
};

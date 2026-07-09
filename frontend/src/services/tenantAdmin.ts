import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function url(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const token = loadStoredAccessToken();
  const response = await fetch(url(path), {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    let message = "Tenant admin data could not be loaded.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the safe default when the server does not return JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

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

export type TenantAdminMember = {
  id: string;
  full_name: string;
  email: string;
  role: "TENANT_ADMIN" | "TENANT_USER";
  status: "active" | "inactive" | "suspended";
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type TenantAdminMemberPayload = {
  full_name: string;
  email: string;
  password?: string;
  role: "tenant_admin" | "user";
  status: "active" | "inactive" | "suspended";
  feature_codes: string[];
};

type TenantAdminMemberListResponse = {
  members: TenantAdminMember[];
};

type TenantAdminFeatureListResponse = {
  features: TenantAdminFeature[];
};

type TenantAdminMemberFeatureCodesResponse = {
  feature_codes: string[];
};

export const tenantAdminApi = {
  getDashboardSummary: () => requestJson<TenantAdminDashboardSummary>("/api/tenant-admin/dashboard"),
  listMembers: () => requestJson<TenantAdminMemberListResponse>("/api/tenant-admin/members").then((response) => response.members),
  createMember: (payload: TenantAdminMemberPayload) =>
    requestJson<TenantAdminMember>("/api/tenant-admin/members", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateMember: (memberId: string, payload: Partial<TenantAdminMemberPayload>) =>
    requestJson<TenantAdminMember>(`/api/tenant-admin/members/${memberId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteMember: (memberId: string) =>
    requestJson<void>(`/api/tenant-admin/members/${memberId}`, {
      method: "DELETE",
    }),
  listMemberFeatures: async (memberId: string) => {
    const response = await requestJson<TenantAdminMemberFeatureCodesResponse>(`/api/tenant-admin/members/${memberId}/features`);
    return response.feature_codes;
  },
  updateMemberFeatures: (memberId: string, featureCodes: string[]) =>
    requestJson<TenantAdminMemberFeatureCodesResponse>(`/api/tenant-admin/members/${memberId}/features`, {
      method: "PUT",
      body: JSON.stringify({ feature_codes: featureCodes }),
    }).then((response) => response.feature_codes),
  listFeatures: () => requestJson<TenantAdminFeatureListResponse>("/api/tenant-admin/features").then((response) => response.features),
};

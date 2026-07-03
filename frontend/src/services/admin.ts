import type { Tenant } from '@/types';
import { loadStoredAccessToken } from '@/services/auth';

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

type RequestInitJson = RequestInit & {
  body?: string;
};

type AdminTenantPayload = {
  full_name: string;
  email: string;
  phone?: string;
  password: string;
  organization_name: string;
  slug?: string;
  logo_url?: string;
  address?: string;
  status: string;
  industry: string;
  max_users: number;
  max_devices: number;
  enabled_modules: string[];
};

type AdminTenantUpdatePayload = Partial<{
  name: string;
  slug: string;
  logo_url: string;
  address: string;
  status: string;
  industry: string;
  admin_name: string;
  admin_email: string;
  phone: string;
  max_users: number;
  max_devices: number;
  enabled_modules: string[];
}>;

type AdminFeaturePayload = {
  feature_name: string;
  feature_code: string;
  description?: string;
  status: string;
};

type RawAdminTenant = {
  id: string;
  name: string;
  slug: string;
  code: string;
  plan: string;
  status: string;
  industry: string;
  logo_url: string | null;
  address: string | null;
  admin_name: string | null;
  admin_email: string | null;
  phone: string | null;
  max_users: number;
  max_devices: number;
  features_count: number;
  enabled_modules: string[];
  users: number;
  sites: number;
  alerts_today: number;
  cameras: number;
  created_at: string;
  updated_at: string;
};

type RawTenantUser = {
  id: string;
  email: string;
  full_name: string;
  role: string;
  tenant_id: string | null;
  is_active: boolean;
  created_at: string;
};

type RawFeature = {
  id: string;
  feature_name: string;
  feature_code: string;
  description: string | null;
  status: string;
  created_at: string;
  updated_at: string;
};

type RawDashboardSummary = {
  total_tenants: number;
  active_tenants: number;
  total_tenant_admins: number;
  total_users: number;
  total_features: number;
  active_sessions: number;
};

type RawAuditLog = {
  id: string;
  user: string;
  action: string;
  entity: string;
  entity_id: string | null;
  note: string | null;
  details: Record<string, unknown> | null;
  timestamp: string;
};

type RawTenantDetails = {
  tenant: RawAdminTenant;
  admins: RawTenantUser[];
  users: RawTenantUser[];
  assigned_features: RawFeature[];
  activity_summary: Record<string, number>;
};

type RawListResponse = {
  features: RawFeature[];
};

function buildApiUrl(path: string) {
  const normalizedPath = path.startsWith('/') ? path : '/' + path;
  if (!API_BASE) return normalizedPath;
  if (API_BASE.endsWith('/api') && normalizedPath.startsWith('/api/')) {
    return API_BASE + normalizedPath.slice(4);
  }
  return API_BASE + normalizedPath;
}

function authHeaders() {
  const token = loadStoredAccessToken();
  return token ? { Authorization: 'Bearer ' + token } : {};
}

function normalizeTenant(raw: RawAdminTenant): AdminTenant {
  return {
    ...raw,
    enabledModules: raw.enabled_modules ?? [],
    alertsToday: raw.alerts_today,
    maxUsers: raw.max_users,
    maxDevices: raw.max_devices,
    featuresCount: raw.features_count,
    adminName: raw.admin_name ?? undefined,
    adminEmail: raw.admin_email ?? undefined,
    phone: raw.phone ?? undefined,
    logo_url: raw.logo_url ?? undefined,
    address: raw.address ?? undefined,
  };
}

function normalizeUser(raw: RawTenantUser): AdminTenantUser {
  return {
    id: raw.id,
    email: raw.email,
    name: raw.full_name,
    role: raw.role,
    tenantId: raw.tenant_id ?? '',
    isActive: raw.is_active,
    createdAt: raw.created_at,
  };
}

function normalizeFeature(raw: RawFeature): AdminFeatureDefinition {
  return raw;
}

function normalizeAuditLog(raw: RawAuditLog): AdminAuditLog {
  return raw;
}

async function requestJson<T>(path: string, init?: RequestInitJson): Promise<T> {
  const response = await fetch(buildApiUrl(path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    let message = 'Request failed.';
    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Keep default error.
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export type AdminTenant = Tenant & {
  slug: string;
  industry: string;
  logo_url?: string;
  address?: string;
  adminName?: string;
  adminEmail?: string;
  phone?: string;
  maxUsers: number;
  maxDevices: number;
  featuresCount: number;
  enabledModules: string[];
  users: number;
  sites: number;
  alertsToday: number;
  cameras: number;
};

export type AdminFeatureDefinition = RawFeature;
export type AdminTenantUser = {
  id: string;
  email: string;
  name: string;
  role: string;
  tenantId: string;
  isActive: boolean;
  createdAt: string;
};
export type AdminDashboardSummary = RawDashboardSummary;
export type AdminAuditLog = RawAuditLog;
export type AdminTenantDetails = {
  tenant: AdminTenant;
  admins: AdminTenantUser[];
  users: AdminTenantUser[];
  assignedFeatures: AdminFeatureDefinition[];
  activitySummary: Record<string, number>;
};

export const adminApi = {
  getDashboardSummary: () => requestJson<AdminDashboardSummary>('/api/admin/summary'),
  listTenants: async () => {
    const response = await requestJson<RawAdminTenant[]>('/api/admin/tenants');
    return response.map(normalizeTenant);
  },
  getTenant: async (tenantId: string) => {
    const response = await requestJson<RawAdminTenant>('/api/admin/tenants/' + tenantId);
    return normalizeTenant(response);
  },
  getTenantDetails: async (tenantId: string) => {
    const response = await requestJson<RawTenantDetails>('/api/admin/tenants/' + tenantId + '/details');
    return {
      tenant: normalizeTenant(response.tenant),
      admins: response.admins.map(normalizeUser),
      users: response.users.map(normalizeUser),
      assignedFeatures: response.assigned_features.map(normalizeFeature),
      activitySummary: response.activity_summary,
    } satisfies AdminTenantDetails;
  },
  createTenant: (payload: AdminTenantPayload) =>
    requestJson<RawAdminTenant>('/api/admin/tenants', {
      method: 'POST',
      body: JSON.stringify(payload),
    }).then(normalizeTenant),
  updateTenant: (tenantId: string, payload: AdminTenantUpdatePayload) =>
    requestJson<RawAdminTenant>('/api/admin/tenants/' + tenantId, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }).then(normalizeTenant),
  deleteTenant: (tenantId: string) =>
    requestJson<void>('/api/admin/tenants/' + tenantId, {
      method: 'DELETE',
    }),
  listAuditLogs: async () => {
    const response = await requestJson<{ logs: RawAuditLog[] }>('/api/admin/audit-logs');
    return response.logs.map(normalizeAuditLog);
  },
  listFeatures: async () => {
    const response = await requestJson<RawListResponse>('/api/super-admin/features');
    return { features: response.features.map(normalizeFeature) };
  },
  createFeature: (payload: AdminFeaturePayload) =>
    requestJson<RawFeature>('/api/super-admin/features', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  updateFeature: (featureId: string, payload: Partial<AdminFeaturePayload>) =>
    requestJson<RawFeature>('/api/super-admin/features/' + featureId, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
  deleteFeature: (featureId: string) =>
    requestJson<void>('/api/super-admin/features/' + featureId, {
      method: 'DELETE',
    }),
  getTenantModules: (tenantId: string) => requestJson('/api/admin/tenants/' + tenantId + '/modules'),
  replaceTenantModules: (tenantId: string, enabledModules: string[]) =>
    requestJson('/api/admin/tenants/' + tenantId + '/modules', {
      method: 'PATCH',
      body: JSON.stringify({ enabled_modules: enabledModules }),
    }),
  toggleTenantModule: (tenantId: string, moduleName: string, enabled: boolean) =>
    requestJson('/api/admin/tenants/' + tenantId + '/modules/' + moduleName, {
      method: 'PATCH',
      body: JSON.stringify({ enabled }),
    }),
};

export type AdminFaceSettings = {
  id: string;
  tenant_id: string;
  face_match_threshold: number;
  min_face_images: number;
  recommended_face_images: number;
  max_face_images: number;
  min_face_size_px: number;
  min_resolution_width: number;
  min_resolution_height: number;
  max_blur_score: number;
  min_brightness: number;
  max_brightness: number;
  embedding_model: string;
  embedding_version?: string | null;
  embedding_dimension: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type AdminFaceSettingsPayload = Partial<{
  face_match_threshold: number;
  min_face_images: number;
  recommended_face_images: number;
  max_face_images: number;
  min_face_size_px: number;
  min_resolution_width: number;
  min_resolution_height: number;
  max_blur_score: number;
  min_brightness: number;
  max_brightness: number;
  embedding_model: string;
  embedding_version: string | null;
  embedding_dimension: number;
  is_active: boolean;
}>;

Object.assign(adminApi, {
  getTenantFaceSettings: (tenantId: string) => requestJson<AdminFaceSettings>(`/api/admin/tenants/${tenantId}/face-settings`),
  updateTenantFaceSettings: (tenantId: string, payload: AdminFaceSettingsPayload) =>
    requestJson<AdminFaceSettings>(`/api/admin/tenants/${tenantId}/face-settings`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    }),
});

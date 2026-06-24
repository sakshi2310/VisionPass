import type { Tenant } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`API request failed (${response.status})`);
  }

  return (await response.json()) as T;
}

export const api = {
  getTenants: () => request<Tenant[]>("/tenants"),
  getTenant: (tenantId: string) => request<Tenant>(`/tenants/${tenantId}`),
  updateTenantModules: (tenantId: string, enabledModules: string[]) =>
    request<Tenant>(`/tenants/${tenantId}/modules`, {
      method: "PATCH",
      body: JSON.stringify({ enabledModules }),
    }),
};

export { API_BASE_URL };

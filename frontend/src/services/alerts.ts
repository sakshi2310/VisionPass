import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type AlertStatus = "open" | "acknowledged" | "resolved";
export type AlertSeverity = "low" | "medium" | "high" | "critical";

export type Alert = {
  id: string;
  tenant_id: string;
  alert_type: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  status: AlertStatus;
  source_type: string;
  source_id?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  acknowledged_at?: string | null;
  resolved_at?: string | null;
};

function url(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = loadStoredAccessToken();
  const response = await fetch(url(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = "Alert request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep safe default.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const alertsApi = {
  list: async (status?: AlertStatus) => (
    await request<{ alerts: Alert[] }>(`/api/alerts${status ? `?status=${status}` : ""}`)
  ).alerts,
  get: (id: string) => request<Alert>(`/api/alerts/${id}`),
  acknowledge: (id: string) => request<Alert>(`/api/alerts/${id}/acknowledge`, { method: "POST" }),
  resolve: (id: string) => request<Alert>(`/api/alerts/${id}/resolve`, { method: "POST" }),
};

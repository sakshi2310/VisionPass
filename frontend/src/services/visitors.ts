import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type VisitorStatus = "expected" | "checked_in" | "checked_out" | "blocked";

export type Visitor = {
  id: string;
  tenant_id: string;
  full_name: string;
  phone: string;
  email?: string | null;
  company?: string | null;
  purpose: string;
  host_employee_id?: string | null;
  photo_path?: string | null;
  status: VisitorStatus;
  created_at: string;
  updated_at: string;
};

export type VisitorVisit = {
  id: string;
  tenant_id: string;
  visitor_id: string;
  check_in_time: string;
  check_out_time?: string | null;
  access_status: string;
  notes?: string | null;
  created_at: string;
};

export type VisitorDetail = Visitor & { visits: VisitorVisit[] };
export type VisitorPayload = Omit<Visitor, "id" | "tenant_id" | "created_at" | "updated_at">;

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
    let message = "Visitor request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep default for non-JSON errors.
    }
    throw new Error(message);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const visitorsApi = {
  list: async () => (await request<{ visitors: Visitor[] }>("/api/visitors")).visitors,
  get: (id: string) => request<VisitorDetail>(`/api/visitors/${id}`),
  create: (payload: VisitorPayload) => request<Visitor>("/api/visitors", { method: "POST", body: JSON.stringify(payload) }),
  update: (id: string, payload: Partial<VisitorPayload>) => request<Visitor>(`/api/visitors/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  remove: (id: string) => request<void>(`/api/visitors/${id}`, { method: "DELETE" }),
  checkIn: (id: string) => request(`/api/visitors/${id}/check-in`, { method: "POST", body: JSON.stringify({ access_status: "granted" }) }),
  checkOut: (id: string) => request(`/api/visitors/${id}/check-out`, { method: "POST", body: JSON.stringify({}) }),
};

import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type AccessDecision = "granted" | "denied" | "manual_review";

export type AccessLog = {
  id: string;
  tenant_id: string;
  employee_id?: string | null;
  visitor_id?: string | null;
  camera_id?: string | null;
  decision: AccessDecision;
  reason: string;
  confidence?: number | null;
  created_at: string;
  identity_name?: string | null;
  camera_name?: string | null;
};

function url(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

async function get<T>(path: string): Promise<T> {
  const token = loadStoredAccessToken();
  const response = await fetch(url(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let message = "Access logs could not be loaded.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the safe default.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const accessControlApi = {
  logs: async (decision?: AccessDecision) => (
    await get<{ logs: AccessLog[] }>(`/api/access/logs${decision ? `?decision=${decision}` : ""}`)
  ).logs,
};

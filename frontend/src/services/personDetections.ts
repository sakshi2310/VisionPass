import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type PersonDetectionMatchType = "staff" | "visitor" | "unknown";
export type PersonDetectionStatus = "new" | "reviewed" | "suspicious" | "converted_to_visitor" | "converted_to_staff" | "ignored";

export type PersonDetection = {
  id: string;
  tenant_id: string;
  camera_id: string;
  zone_id?: string | null;
  image_path?: string | null;
  detected_at: string;
  first_seen_at: string;
  last_seen_at: string;
  seen_count: number;
  snapshot_quality_score?: number | null;
  face_embedding?: number[] | null;
  match_type: PersonDetectionMatchType;
  matched_staff_id?: string | null;
  matched_visitor_id?: string | null;
  status: PersonDetectionStatus;
  note?: string | null;
  created_at: string;
  updated_at: string;
};

export type PersonDetectionAddVisitorPayload = {
  name?: string;
  phone?: string | null;
  purpose?: string | null;
  status?: "active" | "important" | "blocked";
  notes?: string | null;
  visitor_id?: string | null;
};

export type PersonDetectionAddStaffPayload = {
  full_name: string;
  employee_code?: string | null;
  department?: string | null;
  designation?: string | null;
  mobile?: string | null;
  email?: string | null;
  joining_date?: string | null;
  status?: "active" | "inactive";
};

type ListResponse = {
  detections: PersonDetection[];
};

type DetailResponse = PersonDetection;

type AddVisitorResponse = {
  visitor: Record<string, unknown>;
  visit: Record<string, unknown>;
  person_detection: PersonDetection;
};

type AddStaffResponse = {
  employee: Record<string, unknown>;
  face_profile: Record<string, unknown>;
  person_detection: PersonDetection;
};

function apiUrl(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = loadStoredAccessToken();
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let message = "Person detection request failed.";
    try {
      const payload = (await response.json()) as { detail?: string };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      }
    } catch {
      // Ignore non-JSON error bodies.
    }
    throw new Error(message);
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T);
}

export const personDetectionsApi = {
  list: (params?: { cameraId?: string; status?: string; matchType?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.cameraId) query.set("camera_id", params.cameraId);
    if (params?.status) query.set("status", params.status);
    if (params?.matchType) query.set("match_type", params.matchType);
    if (typeof params?.limit === "number") query.set("limit", String(params.limit));
    if (typeof params?.offset === "number") query.set("offset", String(params.offset));
    return request<ListResponse>(`/api/person-detections${query.toString() ? `?${query}` : ""}`).then((response) => response.detections);
  },
  get: (id: string) => request<DetailResponse>(`/api/person-detections/${id}`),
  note: (id: string, note: string) => request<DetailResponse>(`/api/person-detections/${id}/note`, { method: "POST", body: JSON.stringify({ note }) }),
  ignore: (id: string) => request<DetailResponse>(`/api/person-detections/${id}/ignore`, { method: "POST" }),
  addVisitor: (id: string, payload: PersonDetectionAddVisitorPayload) =>
    request<AddVisitorResponse>(`/api/person-detections/${id}/add-visitor`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  addStaff: (id: string, payload: PersonDetectionAddStaffPayload) =>
    request<AddStaffResponse>(`/api/person-detections/${id}/add-staff`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  photoUrl: (id: string) => apiUrl(`/api/person-detections/${id}/photo`),
  fetchPhotoBlob: async (id: string) => {
    const token = loadStoredAccessToken();
    const response = await fetch(apiUrl(`/api/person-detections/${id}/photo`), {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) {
      throw new Error("Person detection photo could not be loaded.");
    }
    return response.blob();
  },
};

export const unknownReviewApi = {
  list: (params?: { cameraId?: string; zoneId?: string; status?: string; limit?: number; offset?: number }) => {
    const query = new URLSearchParams();
    if (params?.cameraId) query.set("camera_id", params.cameraId);
    if (params?.zoneId) query.set("zone_id", params.zoneId);
    if (params?.status) query.set("status", params.status);
    if (typeof params?.limit === "number") query.set("limit", String(params.limit));
    if (typeof params?.offset === "number") query.set("offset", String(params.offset));
    return request<ListResponse>(`/api/unknown-review${query.toString() ? `?${query}` : ""}`).then((response) => response.detections);
  },
  note: (id: string, note: string) => request<DetailResponse>(`/api/unknown-review/${id}/note`, { method: "PATCH", body: JSON.stringify({ note }) }),
  markReviewed: (id: string) => request<DetailResponse>(`/api/unknown-review/${id}/mark-reviewed`, { method: "POST" }),
  markSuspicious: (id: string) => request<DetailResponse>(`/api/unknown-review/${id}/mark-suspicious`, { method: "POST" }),
  ignore: (id: string) => request<DetailResponse>(`/api/unknown-review/${id}/ignore`, { method: "POST" }),
  addVisitor: (id: string, payload: PersonDetectionAddVisitorPayload) =>
    request<AddVisitorResponse>(`/api/unknown-review/${id}/add-visitor`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

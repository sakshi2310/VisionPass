import { loadStoredAccessToken } from "@/services/auth";
import type {
  Employee,
  EmployeeFaceEnrollmentResponse,
  EmployeeFaceImageListResponse,
  EmployeeFaceProfile,
  EmployeeListResponse,
  EmployeePayload,
  EmployeeUpdatePayload,
  FaceImageValidationResult,
} from "@/services/clientAdminAttendance";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

function apiUrl(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

function authHeaders(init?: RequestInit) {
  const token = loadStoredAccessToken();
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(init?.headers ?? {}),
  };
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(init),
    },
  });
  return parseResponse<T>(response);
}

async function requestForm<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: authHeaders(init),
  });
  return parseResponse<T>(response);
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = "Staff request failed.";
    try {
      const payload = (await response.json()) as { detail?: string | { message?: string; code?: string; validation_results?: FaceImageValidationResult[] } };
      if (typeof payload.detail === "string") {
        message = payload.detail;
      } else if (payload.detail && typeof payload.detail === "object") {
        message = payload.detail.message ?? message;
      }
    } catch {
      // Ignore non-JSON error bodies.
    }
    throw new Error(message);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type StaffFaceEnrollmentPayload = {
  files: File[];
  re_enroll?: boolean;
};

function faceEnrollmentForm(payload: StaffFaceEnrollmentPayload): FormData {
  const form = new FormData();
  payload.files.forEach((file) => form.append("files", file, file.name));
  form.append("re_enroll", String(payload.re_enroll ?? false));
  return form;
}

export const staffApi = {
  list: async (params?: { search?: string; department?: string }) => {
    const query = new URLSearchParams();
    if (params?.search) query.set("search", params.search);
    if (params?.department) query.set("department", params.department);
    const response = await requestJson<EmployeeListResponse>(`/api/staff${query.toString() ? `?${query}` : ""}`);
    return response.employees;
  },
  get: (id: string) => requestJson<Employee>(`/api/staff/${id}`),
  create: (payload: EmployeePayload) =>
    requestJson<Employee>("/api/staff", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  update: (id: string, payload: EmployeeUpdatePayload) =>
    requestJson<Employee>(`/api/staff/${id}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  activate: (id: string) =>
    requestJson<Employee>(`/api/staff/${id}/activate`, {
      method: "PATCH",
    }),
  deactivate: (id: string) =>
    requestJson<Employee>(`/api/staff/${id}/deactivate`, {
      method: "PATCH",
    }),
  remove: (id: string) =>
    requestJson<void>(`/api/staff/${id}`, {
      method: "DELETE",
    }),
  faceProfile: (id: string) => requestJson<EmployeeFaceProfile>(`/api/staff/${id}/face-profile`),
  faceImages: (id: string) => requestJson<EmployeeFaceImageListResponse>(`/api/staff/${id}/face-images`),
  enrollFaces: (id: string, payload: StaffFaceEnrollmentPayload) =>
    requestForm<EmployeeFaceEnrollmentResponse>(`/api/staff/${id}/face-images`, {
      method: "POST",
      body: faceEnrollmentForm(payload),
    }),
};

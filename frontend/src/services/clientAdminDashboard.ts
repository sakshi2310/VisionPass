import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type DashboardSummary = {
  total_employees: number;
  active_employees: number;
  today_present: number;
  today_absent: number;
  today_late: number;
  active_cameras: number;
  offline_cameras: number;
  unknown_face_alerts: number;
};

export type DashboardAttendanceEvent = {
  id: string;
  employee_id: string;
  employee_name: string;
  employee_code: string;
  event_type: string;
  source: string;
  camera_id?: string | null;
  camera_name?: string | null;
  confidence?: number | null;
  event_time: string;
};

export type DashboardRecognitionAttempt = {
  id: string;
  camera_id: string;
  camera_name: string;
  employee_id?: string | null;
  employee_name?: string | null;
  recognition_status: string;
  confidence?: number | null;
  created_at: string;
};

export type DashboardRecentActivity = {
  attendance_events: DashboardAttendanceEvent[];
  recognition_attempts: DashboardRecognitionAttempt[];
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
    let message = "Dashboard data could not be loaded.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Use the safe default for non-JSON errors.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const clientAdminDashboardApi = {
  getSummary: () => get<DashboardSummary>("/api/client-admin/dashboard/summary"),
  getRecentActivity: () => get<DashboardRecentActivity>("/api/client-admin/dashboard/recent-activity"),
};

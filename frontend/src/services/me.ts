import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type MeShift = {
  id: string;
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: number;
};

export type MeMonthlySummary = {
  month: string;
  present: number;
  late: number;
  half_day: number;
  absent: number;
  holidays: number;
  total_working_days: number;
  total_work_hours: number;
  attendance_percentage: number;
};

export type MeDashboard = {
  today_status: string;
  check_in_time?: string | null;
  check_out_time?: string | null;
  working_hours: number;
  current_shift?: MeShift | null;
  monthly_summary: MeMonthlySummary;
  employee_linked: boolean;
};

export type MeAttendanceDay = {
  id: string;
  attendance_date: string;
  first_check_in?: string | null;
  last_check_out?: string | null;
  total_work_minutes: number;
  working_hours: number;
  status: string;
  shift?: MeShift | null;
};

export type MeAttendance = {
  month: string;
  days: MeAttendanceDay[];
  summary: MeMonthlySummary;
  employee_linked: boolean;
};

export type MeProfile = {
  member_id: string;
  employee_id?: string | null;
  full_name: string;
  email: string;
  phone?: string | null;
  department?: string | null;
  designation?: string | null;
  employee_code?: string | null;
  employee_type?: string | null;
  joining_date?: string | null;
  status: string;
  shift?: MeShift | null;
  face_enrollment_status: string;
  face_count: number;
};

export type MeNotification = {
  id: string;
  type: "attendance" | "profile";
  title: string;
  message: string;
  severity: "info" | "warning";
  created_at: string;
};

function buildUrl(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

async function get<T>(path: string): Promise<T> {
  const token = loadStoredAccessToken();
  const response = await fetch(buildUrl(path), {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!response.ok) {
    let message = "Your data could not be loaded.";
    try {
      const payload = (await response.json()) as { detail?: string };
      message = payload.detail ?? message;
    } catch {
      // Keep the safe default for non-JSON responses.
    }
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const meApi = {
  dashboard: () => get<MeDashboard>("/api/me/dashboard"),
  attendance: (month?: string) => get<MeAttendance>(`/api/me/attendance${month ? `?month=${month}` : ""}`),
  profile: () => get<MeProfile>("/api/me/profile"),
  notifications: async () => (await get<{ notifications: MeNotification[] }>("/api/me/notifications")).notifications,
};

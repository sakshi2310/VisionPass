import { loadStoredAccessToken } from "@/services/auth";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export type ReportKind = "attendance" | "employees" | "visitors" | "person_detections" | "unknown_review" | "cameras" | "recognition" | "access";

export type ReportFilters = {
  start_date?: string;
  end_date?: string;
  employee_id?: string;
  department?: string;
  status?: string;
  camera_id?: string;
  zone_id?: string;
  match_type?: string;
  event_type?: string;
};

export type ReportResult = {
  items: Record<string, unknown>[];
  total: number;
};

function apiUrl(path: string) {
  if (!API_BASE) return path;
  if (API_BASE.endsWith("/api") && path.startsWith("/api/")) return `${API_BASE}${path.slice(4)}`;
  return `${API_BASE}${path}`;
}

const REPORT_PATHS: Record<ReportKind, string> = {
  attendance: "/api/reports/attendance",
  employees: "/api/reports/employees",
  visitors: "/api/reports/visitors",
  person_detections: "/api/reports/person-detections",
  unknown_review: "/api/reports/unknown-review",
  cameras: "/api/reports/cameras",
  recognition: "/api/reports/recognition",
  access: "/api/reports/access",
};

export function reportQuery(filters: ReportFilters) {
  const query = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  return query.toString();
}

export async function fetchReport(kind: ReportKind, filters: ReportFilters): Promise<ReportResult> {
  const query = reportQuery(filters);
  const response = await fetch(apiUrl(`${REPORT_PATHS[kind]}${query ? `?${query}` : ""}`), {
    headers: { Authorization: `Bearer ${loadStoredAccessToken() ?? ""}` },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({})) as { detail?: string };
    throw new Error(payload.detail ?? `Unable to load ${kind} report.`);
  }
  return response.json() as Promise<ReportResult>;
}

export async function downloadReport(kind: "attendance" | "access" | "visitors" | "person_detections" | "unknown_review", filters: ReportFilters) {
  const query = reportQuery(filters);
  const exportPaths: Record<"attendance" | "access" | "visitors" | "person_detections" | "unknown_review", string> = {
    attendance: "/api/reports/attendance/export.csv",
    access: "/api/reports/access/export.csv",
    visitors: "/api/reports/visitors/export.csv",
    person_detections: "/api/reports/person-detections/export.csv",
    unknown_review: "/api/reports/unknown-review/export.csv",
  };
  const response = await fetch(apiUrl(`${exportPaths[kind]}${query ? `?${query}` : ""}`), {
    headers: { Authorization: `Bearer ${loadStoredAccessToken() ?? ""}` },
  });
  if (!response.ok) throw new Error("Unable to export this report.");
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${kind}-report.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}

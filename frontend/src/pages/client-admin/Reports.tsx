import { useEffect, useMemo, useState } from "react";
import { Download, FileBarChart, RefreshCw, SearchX } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { fetchCameras, fetchEmployees, type Camera, type Employee } from "@/services/clientAdminAttendance";
import {
  downloadReport,
  fetchReport,
  type ReportFilters,
  type ReportKind,
} from "@/services/reports";

const reportNames: Record<ReportKind, string> = {
  attendance: "Attendance",
  employees: "Employees",
  visitors: "Visitors",
  cameras: "Cameras",
  recognition: "Recognition",
  access: "Access logs",
};

const columns: Record<ReportKind, { key: string; label: string }[]> = {
  attendance: [
    { key: "attendance_date", label: "Date" }, { key: "employee_name", label: "Employee" },
    { key: "department", label: "Department" }, { key: "status", label: "Status" },
    { key: "first_check_in", label: "First in" }, { key: "last_check_out", label: "Last out" },
    { key: "total_work_minutes", label: "Work minutes" },
  ],
  employees: [
    { key: "employee_code", label: "Code" }, { key: "full_name", label: "Employee" },
    { key: "department", label: "Department" }, { key: "designation", label: "Designation" },
    { key: "employee_type", label: "Type" }, { key: "status", label: "Status" },
    { key: "joining_date", label: "Joined" },
  ],
  visitors: [
    { key: "full_name", label: "Visitor" }, { key: "company", label: "Company" },
    { key: "purpose", label: "Purpose" }, { key: "host_employee_name", label: "Host" },
    { key: "status", label: "Status" }, { key: "check_in_time", label: "Check in" },
    { key: "check_out_time", label: "Check out" },
  ],
  cameras: [
    { key: "name", label: "Camera" }, { key: "location", label: "Location" },
    { key: "camera_type", label: "Type" }, { key: "status", label: "Status" },
    { key: "health_status", label: "Health" }, { key: "event_count", label: "Events" },
    { key: "last_seen_at", label: "Last seen" },
  ],
  recognition: [
    { key: "created_at", label: "Time" }, { key: "employee_name", label: "Employee" },
    { key: "camera_name", label: "Camera" }, { key: "event_type", label: "Event" },
    { key: "recognition_status", label: "Status" }, { key: "confidence", label: "Confidence" },
  ],
  access: [
    { key: "created_at", label: "Time" }, { key: "identity_name", label: "Identity" },
    { key: "identity_type", label: "Type" }, { key: "camera_name", label: "Camera" },
    { key: "decision", label: "Decision" }, { key: "reason", label: "Reason" },
    { key: "confidence", label: "Confidence" },
  ],
};

const statusOptions: Record<ReportKind, string[]> = {
  attendance: ["present", "late", "half_day", "absent", "holiday"],
  employees: ["active", "inactive"],
  visitors: ["expected", "checked_in", "checked_out", "blocked"],
  cameras: ["active", "inactive", "online", "offline", "error", "unknown"],
  recognition: ["MATCHED", "UNKNOWN", "LOW_CONFIDENCE", "NO_FACE", "MULTIPLE_FACES"],
  access: ["granted", "denied", "manual_review"],
};

const eventOptions: Partial<Record<ReportKind, string[]>> = {
  attendance: ["check_in", "check_out"],
  recognition: ["face_recognition", "attendance_recognition", "frame_processed", "recognition"],
  access: ["employee", "visitor", "unknown"],
};

function formatValue(value: unknown, key: string) {
  if (value === null || value === undefined || value === "") return "—";
  if (key.includes("_at") || key.includes("_in") || key.includes("_out")) {
    const parsed = new Date(String(value));
    if (!Number.isNaN(parsed.getTime())) return parsed.toLocaleString();
  }
  if (key === "confidence" && typeof value === "number") return `${Math.round(value * 100)}%`;
  return String(value).replaceAll("_", " ");
}

const fieldClass = "h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm text-slate-700 outline-none focus:border-brand-400 dark:border-white/10 dark:bg-slate-950 dark:text-slate-200";

export function ReportsPage() {
  const [kind, setKind] = useState<ReportKind>("attendance");
  const [filters, setFilters] = useState<ReportFilters>({});
  const [items, setItems] = useState<Record<string, unknown>[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const queryKey = useMemo(() => JSON.stringify(filters), [filters]);

  useEffect(() => {
    Promise.all([fetchEmployees(), fetchCameras()])
      .then(([employeeRows, cameraRows]) => {
        setEmployees(employeeRows);
        setCameras(cameraRows);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetchReport(kind, filters)
      .then((result) => active && setItems(result.items))
      .catch((reason: Error) => active && setError(reason.message))
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [kind, queryKey]);

  function updateFilter(key: keyof ReportFilters, value: string) {
    setFilters((current) => ({ ...current, [key]: value || undefined }));
  }

  const departments = [...new Set(employees.map((employee) => employee.department).filter(Boolean))] as string[];

  return (
    <div className="grid gap-6">
      <section className="surface-strong flex flex-col justify-between gap-5 p-7 md:flex-row md:items-end">
        <div>
          <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Reports</p>
          <h1 className="mt-2 text-3xl font-semibold text-white">Operational reporting</h1>
          <p className="mt-2 text-sm text-slate-400">Filter live tenant data across attendance, people, cameras, recognition, and access.</p>
        </div>
        {(kind === "attendance" || kind === "access") && (
          <Button
            variant="secondary"
            leftIcon={<Download className="h-4 w-4" />}
            disabled={exporting}
            onClick={async () => {
              setExporting(true);
              try { await downloadReport(kind, filters); } catch (reason) {
                setError(reason instanceof Error ? reason.message : "Export failed.");
              } finally { setExporting(false); }
            }}
          >
            {exporting ? "Exporting..." : "Export CSV"}
          </Button>
        )}
      </section>

      <Card className="p-4">
        <div className="flex flex-wrap gap-2">
          {(Object.keys(reportNames) as ReportKind[]).map((report) => (
            <button
              key={report}
              type="button"
              onClick={() => { setKind(report); setFilters({}); }}
              className={`rounded-xl px-4 py-2 text-sm font-medium transition ${kind === report ? "bg-brand-500 text-white" : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-white/5 dark:text-slate-300"}`}
            >
              {reportNames[report]}
            </button>
          ))}
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <input className={fieldClass} type="date" aria-label="Start date" value={filters.start_date ?? ""} onChange={(event) => updateFilter("start_date", event.target.value)} />
          <input className={fieldClass} type="date" aria-label="End date" value={filters.end_date ?? ""} onChange={(event) => updateFilter("end_date", event.target.value)} />
          {kind !== "cameras" && (
            <select className={fieldClass} aria-label="Employee" value={filters.employee_id ?? ""} onChange={(event) => updateFilter("employee_id", event.target.value)}>
              <option value="">All employees</option>
              {employees.map((employee) => <option key={employee.id} value={employee.id}>{employee.full_name}</option>)}
            </select>
          )}
          {["attendance", "employees", "recognition", "access"].includes(kind) && (
            <select className={fieldClass} aria-label="Department" value={filters.department ?? ""} onChange={(event) => updateFilter("department", event.target.value)}>
              <option value="">All departments</option>
              {departments.map((department) => <option key={department} value={department}>{department}</option>)}
            </select>
          )}
          <select className={fieldClass} aria-label="Status" value={filters.status ?? ""} onChange={(event) => updateFilter("status", event.target.value)}>
            <option value="">All statuses</option>
            {statusOptions[kind].map((status) => <option key={status} value={status}>{status.replaceAll("_", " ")}</option>)}
          </select>
          {!["employees"].includes(kind) && (
            <select className={fieldClass} aria-label="Camera" value={filters.camera_id ?? ""} onChange={(event) => updateFilter("camera_id", event.target.value)}>
              <option value="">All cameras</option>
              {cameras.map((camera) => <option key={camera.id} value={camera.id}>{camera.name}</option>)}
            </select>
          )}
          {eventOptions[kind] && (
            <select className={fieldClass} aria-label="Event type" value={filters.event_type ?? ""} onChange={(event) => updateFilter("event_type", event.target.value)}>
              <option value="">All event types</option>
              {eventOptions[kind]!.map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}
            </select>
          )}
          <Button variant="secondary" onClick={() => setFilters({})}>Clear filters</Button>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="flex items-center gap-3">
            <FileBarChart className="h-5 w-5 text-brand-500" />
            <h2 className="font-semibold text-slate-900 dark:text-white">{reportNames[kind]} report</h2>
          </div>
          {!loading && !error && <Badge tone="info">{items.length} records</Badge>}
        </div>
        {loading ? (
          <div className="flex min-h-64 items-center justify-center gap-3 text-sm text-slate-500">
            <RefreshCw className="h-5 w-5 animate-spin" /> Loading report…
          </div>
        ) : error ? (
          <div className="grid min-h-64 place-items-center p-8 text-center">
            <div><p className="font-medium text-rose-600">Could not load report</p><p className="mt-2 text-sm text-slate-500">{error}</p></div>
          </div>
        ) : items.length === 0 ? (
          <div className="grid min-h-64 place-items-center p-8 text-center text-slate-500">
            <div><SearchX className="mx-auto h-8 w-8" /><p className="mt-3 font-medium">No records match these filters</p><p className="mt-1 text-sm">Try widening the date range or clearing a filter.</p></div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 dark:bg-white/5">
                <tr>{columns[kind].map((column) => <th key={column.key} className="whitespace-nowrap px-5 py-3 font-medium">{column.label}</th>)}</tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                {items.map((item, index) => (
                  <tr key={String(item.id ?? index)} className="text-slate-700 hover:bg-slate-50 dark:text-slate-300 dark:hover:bg-white/[0.03]">
                    {columns[kind].map((column) => <td key={column.key} className="whitespace-nowrap px-5 py-4">{formatValue(item[column.key], column.key)}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

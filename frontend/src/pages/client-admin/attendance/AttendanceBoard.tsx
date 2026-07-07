import { CalendarDays, Clock3, Eye, Loader2, RefreshCw, Search, TimerReset, UserRoundCheck, UserRoundX, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchAttendanceBoard,
  fetchEmployeeAttendanceSummary,
  fetchShifts,
  type AttendanceBoardEmployee,
  type AttendanceBoardResponse,
  type AttendanceBoardStatus,
  type EmployeeAttendanceSummary,
  type AttendanceShift,
} from "@/services/clientAdminAttendance";

const STATUS_OPTIONS: Array<{ value: "all" | AttendanceBoardStatus; label: string }> = [
  { value: "all", label: "All statuses" },
  { value: "present", label: "Present" },
  { value: "late", label: "Late" },
  { value: "half_day", label: "Half day" },
  { value: "absent", label: "Absent" },
  { value: "not_detected", label: "Not detected yet" },
  { value: "holiday", label: "Holiday" },
];

type ToastState = { tone: "success" | "error"; title: string; message: string } | null;

function todayIsoDate() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function formatDateTime(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "short" }).format(new Date(value));
}

function formatDuration(minutes?: number | null) {
  const safe = Math.max(0, Math.round(minutes ?? 0));
  const hours = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${hours}h ${remainder}m`;
}

function statusLabel(status: AttendanceBoardStatus) {
  return status.replace("_", " ");
}

function statusTone(status: AttendanceBoardStatus) {
  if (status === "present") return "success" as const;
  if (status === "late" || status === "half_day") return "warning" as const;
  if (status === "absent") return "danger" as const;
  if (status === "holiday") return "info" as const;
  return "neutral" as const;
}

function StatCard({ label, value, icon }: { label: string; value: number; icon: ReactNode }) {
  return (
    <Card className="flex items-center justify-between p-5">
      <div>
        <p className="text-sm text-slate-500 dark:text-slate-400">{label}</p>
        <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{value}</p>
      </div>
      <div className="grid h-11 w-11 place-items-center rounded-2xl bg-cyan-500/10 text-cyan-400">{icon}</div>
    </Card>
  );
}

function EmployeeSummaryModal({
  employee,
  date,
  onClose,
}: {
  employee: AttendanceBoardEmployee | null;
  date: string;
  onClose: () => void;
}) {
  const [summary, setSummary] = useState<EmployeeAttendanceSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!employee) return;
    let cancelled = false;
    setLoading(true);
    setError("");
    fetchEmployeeAttendanceSummary(employee.employee_id, date)
      .then((payload) => {
        if (!cancelled) setSummary(payload);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Unable to load employee summary.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [date, employee]);

  if (!employee) return null;

  return (
    <Modal open={Boolean(employee)} onClose={onClose} title="Employee attendance summary" size="lg">
      <div className="grid gap-5">
        <div className="flex flex-col gap-3 rounded-2xl bg-slate-50 p-4 dark:bg-white/5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{employee.employee_name}</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {employee.employee_code} · {employee.department ?? "No department"} · {employee.shift_name ?? "No shift"}
            </p>
          </div>
          <Badge tone={statusTone(employee.status)} className="capitalize">{statusLabel(employee.status)}</Badge>
        </div>

        {loading ? (
          <div className="grid min-h-40 place-items-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : error ? (
          <div className="rounded-2xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm text-rose-600 dark:text-rose-200">{error}</div>
        ) : summary ? (
          <>
            <div className="grid gap-3 sm:grid-cols-4">
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Present time</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDuration(summary.summary?.total_present_minutes)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Absent time</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDuration(summary.summary?.total_absent_minutes)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">First seen</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDateTime(summary.summary?.first_seen_at)}</p>
              </div>
              <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                <p className="text-xs uppercase tracking-wider text-slate-500">Last seen</p>
                <p className="mt-2 font-semibold text-slate-900 dark:text-white">{formatDateTime(summary.summary?.last_seen_at)}</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Presence sessions</h4>
              <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 dark:border-white/10">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 dark:bg-white/5">
                    <tr><th className="p-3">Check in</th><th className="p-3">Check out</th><th className="p-3">Duration</th><th className="p-3">Source</th></tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                    {summary.sessions.length ? summary.sessions.map((session, index) => (
                      <tr key={`${session.check_in}-${index}`}>
                        <td className="p-3">{formatDateTime(session.check_in)}</td>
                        <td className="p-3">{session.is_open ? "Running" : formatDateTime(session.check_out)}</td>
                        <td className="p-3">{formatDuration(session.duration_minutes)}</td>
                        <td className="p-3 capitalize">{session.source ?? "—"}</td>
                      </tr>
                    )) : (
                      <tr><td className="p-4 text-center text-slate-500" colSpan={4}>No presence sessions for this date.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold uppercase tracking-[0.18em] text-slate-500">Detection history</h4>
              <div className="mt-3 grid gap-2">
                {summary.detection_history.length ? summary.detection_history.map((event) => (
                  <div key={event.id} className="flex items-center justify-between rounded-2xl bg-slate-50 p-3 text-sm dark:bg-white/5">
                    <span className="capitalize text-slate-700 dark:text-slate-200">{event.event_type.replace("_", " ")} · {event.source}</span>
                    <span className="text-slate-500">{formatDateTime(event.event_time)}</span>
                  </div>
                )) : <p className="text-sm text-slate-500">No detections recorded for this date.</p>}
              </div>
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
}

export function AttendanceBoardPage() {
  const [date, setDate] = useState(todayIsoDate());
  const [search, setSearch] = useState("");
  const [department, setDepartment] = useState("");
  const [shiftId, setShiftId] = useState("");
  const [status, setStatus] = useState<"all" | AttendanceBoardStatus>("all");
  const [board, setBoard] = useState<AttendanceBoardResponse | null>(null);
  const [shifts, setShifts] = useState<AttendanceShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedEmployee, setSelectedEmployee] = useState<AttendanceBoardEmployee | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle("Vision Pass | Attendance Board");

  const departments = useMemo(() => {
    const values = new Set<string>();
    board?.employees.forEach((employee) => {
      if (employee.department) values.add(employee.department);
    });
    return Array.from(values).sort();
  }, [board]);

  async function loadBoard(options?: { silent?: boolean }) {
    try {
      if (!options?.silent) setLoading(true);
      const payload = await fetchAttendanceBoard({ date, search, department, shiftId, status });
      setBoard(payload);
    } catch (error) {
      setToast({ tone: "error", title: "Attendance board unavailable", message: error instanceof Error ? error.message : "Unable to load attendance board." });
    } finally {
      if (!options?.silent) setLoading(false);
    }
  }

  useEffect(() => {
    fetchShifts().then(setShifts).catch(() => setShifts([]));
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => void loadBoard(), 250);
    return () => window.clearTimeout(handle);
  }, [date, search, department, shiftId, status]);

  useEffect(() => {
    const interval = window.setInterval(() => void loadBoard({ silent: true }), 10000);
    return () => window.clearInterval(interval);
  }, [date, search, department, shiftId, status]);

  const stats = board?.stats ?? { total: 0, present: 0, late: 0, half_day: 0, absent: 0, holiday: 0, not_detected: 0 };

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Attendance board</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Employee presence and absence</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This board shows every active employee for the selected date. Camera recognition updates check-in/check-out records, and this page refreshes automatically every 10 seconds.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadBoard()} disabled={loading}>
            Refresh
          </Button>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <StatCard label="Total employees" value={stats.total} icon={<UserRoundCheck className="h-5 w-5" />} />
        <StatCard label="Present" value={stats.present} icon={<UserRoundCheck className="h-5 w-5" />} />
        <StatCard label="Late / Half day" value={(stats.late ?? 0) + (stats.half_day ?? 0)} icon={<Clock3 className="h-5 w-5" />} />
        <StatCard label="Absent" value={stats.absent} icon={<UserRoundX className="h-5 w-5" />} />
        <StatCard label="Not detected" value={stats.not_detected} icon={<TimerReset className="h-5 w-5" />} />
      </div>

      <Card className="p-5">
        <div className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr_0.8fr_0.8fr_0.8fr]">
          <Input label="Search" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Name, code, email" leftIcon={<Search className="h-4 w-4" />} />
          <Input label="Date" type="date" value={date} onChange={(event) => setDate(event.target.value)} leftIcon={<CalendarDays className="h-4 w-4" />} />
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Department
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={department} onChange={(event) => setDepartment(event.target.value)}>
              <option value="">All departments</option>
              {departments.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Shift
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={shiftId} onChange={(event) => setShiftId(event.target.value)}>
              <option value="">All shifts</option>
              {shifts.map((shift) => <option key={shift.id} value={shift.id}>{shift.name}</option>)}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Status
            <select className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100" value={status} onChange={(event) => setStatus(event.target.value as "all" | AttendanceBoardStatus)}>
              {STATUS_OPTIONS.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
            </select>
          </label>
        </div>
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 p-5 dark:border-white/10">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Employee attendance list</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Click any employee to see sessions and detection history.</p>
        </div>
        {loading ? (
          <div className="grid min-h-64 place-items-center text-slate-500"><Loader2 className="h-7 w-7 animate-spin" /></div>
        ) : board?.employees.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.18em] text-slate-500 dark:bg-white/5">
                <tr>
                  <th className="px-5 py-4">Employee</th>
                  <th className="px-5 py-4">Department</th>
                  <th className="px-5 py-4">Shift</th>
                  <th className="px-5 py-4">Status</th>
                  <th className="px-5 py-4">First seen</th>
                  <th className="px-5 py-4">Last seen</th>
                  <th className="px-5 py-4">Present</th>
                  <th className="px-5 py-4">Absent</th>
                  <th className="px-5 py-4">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                {board.employees.map((employee) => (
                  <tr key={employee.employee_id} className="hover:bg-slate-50/70 dark:hover:bg-white/[0.03]">
                    <td className="px-5 py-4">
                      <button className="text-left" onClick={() => setSelectedEmployee(employee)}>
                        <div className="font-semibold text-slate-900 dark:text-white">{employee.employee_name}</div>
                        <div className="text-xs text-slate-500">{employee.employee_code} · {employee.email}</div>
                      </button>
                    </td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{employee.department ?? "—"}</td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{employee.shift_name ?? "—"}</td>
                    <td className="px-5 py-4"><Badge tone={statusTone(employee.status)} className="capitalize">{statusLabel(employee.status)}</Badge></td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{formatDateTime(employee.first_seen_at)}</td>
                    <td className="px-5 py-4 text-slate-600 dark:text-slate-300">{formatDateTime(employee.last_seen_at)}</td>
                    <td className="px-5 py-4 font-medium text-slate-900 dark:text-white">{formatDuration(employee.total_present_minutes)}</td>
                    <td className="px-5 py-4 font-medium text-slate-900 dark:text-white">{formatDuration(employee.total_absent_minutes)}</td>
                    <td className="px-5 py-4">
                      <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => setSelectedEmployee(employee)}>View</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8"><EmptyState title="No employees found" description="Change filters or add active employees to view attendance." action={<X className="h-6 w-6 text-slate-400" />} /></div>
        )}
      </Card>

      <EmployeeSummaryModal employee={selectedEmployee} date={date} onClose={() => setSelectedEmployee(null)} />
      {toast ? <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} /> : null}
    </div>
  );
}

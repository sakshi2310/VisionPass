import { CalendarDays, Loader2, RefreshCw } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchAttendanceBoard,
  type AttendanceBoardEmployee,
  type AttendanceBoardResponse,
} from "@/services/clientAdminAttendance";

type ToastState = { tone: "success" | "error"; title: string; message: string } | null;

const isDev =
  typeof window !== "undefined" &&
  ["localhost", "127.0.0.1", "::1"].includes(window.location.hostname);

function devLog(message: string, payload?: unknown) {
  if (!isDev) return;
  if (payload === undefined) {
    console.log("[ATTENDANCE_BOARD]", message);
    return;
  }
  console.log("[ATTENDANCE_BOARD]", message, payload);
}

function todayIsoDate() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now.getTime() - offset).toISOString().slice(0, 10);
}

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function Row({
  employee,
  kind,
}: {
  employee: AttendanceBoardEmployee;
  kind: "present" | "absent";
}) {
  const time =
    kind === "present"
      ? employee.check_in_time ?? employee.latest_event_time ?? employee.last_seen_time ?? employee.first_seen_at
      : employee.last_seen_time ?? employee.latest_event_time ?? employee.last_seen_at;
  const label = kind === "present" ? "Present" : "Absent";

  return (
    <tr className="border-t border-slate-200/80 dark:border-white/10">
      <td className="px-4 py-4">
        <div className="font-semibold text-slate-900 dark:text-white">{employee.employee_name}</div>
        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{employee.employee_code ?? employee.employee_id}</div>
      </td>
      <td className="px-4 py-4">
        <Badge tone={kind === "present" ? "success" : "danger"} className="capitalize">
          {label}
        </Badge>
      </td>
      <td className="px-4 py-4 text-sm text-slate-700 dark:text-slate-300">{formatDateTime(time ?? null)}</td>
    </tr>
  );
}

function EmptyTableMessage({ message }: { message: string }) {
  return (
    <div className="p-5">
      <div className="rounded-2xl border border-dashed border-slate-300 p-5 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
        {message}
      </div>
    </div>
  );
}

export function AttendanceBoardPage() {
  const [date, setDate] = useState(todayIsoDate());
  const [board, setBoard] = useState<AttendanceBoardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle("Vision Pass | Attendance Board");

  async function loadBoard() {
    devLog("Attendance Board loads", { selected_date: date });
    setLoading(true);
    try {
      const payload = await fetchAttendanceBoard({ date });
      setBoard(payload);
      devLog("API response received", payload);
      devLog("present_employees count", payload.present_employees?.length ?? 0);
      devLog("absent_employees count", payload.absent_employees?.length ?? 0);
      devLog("debug_summary", payload.debug_summary);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to load attendance board.";
      setToast({ tone: "error", title: "Attendance board unavailable", message });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadBoard();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      void loadBoard();
    }, 5000);
    return () => window.clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [date]);

  function handleRefresh() {
    devLog("Refresh clicked", { selected_date: date });
    void loadBoard();
  }

  const presentEmployees = board?.present_employees ?? [];
  const absentEmployees = board?.absent_employees ?? [];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Attendance board</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Attendance Board</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Use the date filter and refresh button to review live attendance projection for the selected day.
            </p>
          </div>
          <div className="flex items-end gap-3">
            <Input
              label="Date"
              type="date"
              value={date}
              onChange={(event) => setDate(event.target.value)}
              leftIcon={<CalendarDays className="h-4 w-4" />}
            />
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={handleRefresh} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
      </section>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 p-5 dark:border-white/10">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Present Employees</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Employees currently projected as present for the selected date.
          </p>
        </div>
        {loading && !board ? (
          <div className="grid min-h-40 place-items-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : presentEmployees.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.18em] text-slate-500 dark:bg-white/5">
                <tr>
                  <th className="px-4 py-3">Employee</th>
                  <th className="px-4 py-3">Label</th>
                  <th className="px-4 py-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                {presentEmployees.map((employee) => (
                  <Row key={employee.employee_id} employee={employee} kind="present" />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyTableMessage message="No present employees found for this date." />
        )}
      </Card>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 p-5 dark:border-white/10">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent Absent / Not Detected</h2>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Employees projected as absent or not detected for the selected date.
          </p>
        </div>
        {loading && !board ? (
          <div className="grid min-h-40 place-items-center text-slate-500">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
        ) : absentEmployees.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-[0.18em] text-slate-500 dark:bg-white/5">
                <tr>
                  <th className="px-4 py-3">Employee</th>
                  <th className="px-4 py-3">Label</th>
                  <th className="px-4 py-3">Last time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-white/10">
                {absentEmployees.map((employee) => (
                  <Row key={employee.employee_id} employee={employee} kind="absent" />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyTableMessage message="No absent or not detected employees." />
        )}
      </Card>

      {toast ? <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} /> : null}
    </div>
  );
}

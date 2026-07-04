import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePageTitle } from "@/hooks/usePageTitle";
import { meApi, type MeAttendance } from "@/services/me";
import { formatTime } from "@/utils/format";

function badgeTone(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  if (status === "present") return "success";
  if (status === "late" || status === "half_day") return "warning";
  if (status === "absent") return "danger";
  if (status === "holiday") return "info";
  return "neutral";
}

function changeMonth(month: string, delta: number) {
  const [year, monthNumber] = month.split("-").map(Number);
  const date = new Date(year, monthNumber - 1 + delta, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export function TenantUserAttendance() {
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
  });
  const [data, setData] = useState<MeAttendance | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | My Attendance");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await meApi.attendance(month));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Attendance could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [month]);

  useEffect(() => void load(), [load]);

  const calendar = useMemo(() => {
    const [year, monthNumber] = month.split("-").map(Number);
    const count = new Date(year, monthNumber, 0).getDate();
    const offset = new Date(year, monthNumber - 1, 1).getDay();
    const byDate = new Map(data?.days.map((day) => [day.attendance_date, day]) ?? []);
    return { count, offset, byDate, year, monthNumber };
  }, [data, month]);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">My attendance</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Daily history and calendar</h1>
            <p className="mt-2 text-sm text-slate-400">Only attendance linked to your own employee record appears here.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => setMonth(changeMonth(month, -1))}><ChevronLeft className="h-4 w-4" /></Button>
            <div className="min-w-36 text-center text-sm font-medium text-white">
              {new Date(`${month}-01T00:00:00`).toLocaleDateString(undefined, { month: "long", year: "numeric" })}
            </div>
            <Button variant="secondary" size="sm" onClick={() => setMonth(changeMonth(month, 1))}><ChevronRight className="h-4 w-4" /></Button>
            <Button variant="secondary" size="sm" onClick={() => void load()} disabled={loading}><RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} /></Button>
          </div>
        </div>
      </section>

      {error ? <EmptyState title="Attendance unavailable" description={error} action={<Button onClick={() => void load()}>Try again</Button>} /> : null}
      {!error && !loading && data && !data.employee_linked ? <EmptyState title="Attendance profile not linked" description="Ask your administrator to link your account to an employee record." /> : null}

      {!error && (loading || data?.employee_linked) ? (
        <>
          <Card>
            <div className="grid grid-cols-7 gap-2 text-center text-xs font-medium uppercase text-slate-500">
              {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((day) => <div key={day} className="py-2">{day}</div>)}
              {Array.from({ length: calendar.offset }).map((_, index) => <div key={`empty-${index}`} />)}
              {Array.from({ length: calendar.count }).map((_, index) => {
                const dayNumber = index + 1;
                const key = `${calendar.year}-${String(calendar.monthNumber).padStart(2, "0")}-${String(dayNumber).padStart(2, "0")}`;
                const record = calendar.byDate.get(key);
                return (
                  <div key={key} className="min-h-20 rounded-2xl border border-slate-200 p-2 text-left dark:border-white/10">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{dayNumber}</span>
                    {record ? <div className="mt-2"><Badge tone={badgeTone(record.status)}>{record.status.replace("_", " ")}</Badge></div> : null}
                  </div>
                );
              })}
            </div>
          </Card>

          <Card>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Daily records</h2>
            {loading ? (
              <div className="mt-4 grid gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-14 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" />)}</div>
            ) : data?.days.length ? (
              <div className="mt-4 overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs uppercase text-slate-500"><tr><th className="pb-3">Date</th><th className="pb-3">Status</th><th className="pb-3">Check-in</th><th className="pb-3">Check-out</th><th className="pb-3">Hours</th></tr></thead>
                  <tbody>
                    {data.days.map((day) => (
                      <tr key={day.id} className="border-t border-slate-200 dark:border-white/10">
                        <td className="py-4">{new Date(`${day.attendance_date}T00:00:00`).toLocaleDateString()}</td>
                        <td className="py-4"><Badge tone={badgeTone(day.status)}>{day.status.replace("_", " ")}</Badge></td>
                        <td className="py-4">{day.first_check_in ? formatTime(day.first_check_in) : "—"}</td>
                        <td className="py-4">{day.last_check_out ? formatTime(day.last_check_out) : "—"}</td>
                        <td className="py-4">{day.working_hours}h</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <div className="mt-4 rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500 dark:border-white/10">No attendance records for this month.</div>}
          </Card>
        </>
      ) : null}
    </div>
  );
}

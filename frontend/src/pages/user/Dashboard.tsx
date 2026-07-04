import { CalendarCheck2, Clock3, LogIn, LogOut, RefreshCw, Timer } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { meApi, type MeDashboard } from "@/services/me";
import { formatTime } from "@/utils/format";

function tone(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "present") return "success";
  if (status === "late" || status === "half_day") return "warning";
  if (status === "absent") return "danger";
  return "neutral";
}

export function TenantUserDashboard() {
  const { user } = useApp();
  const [data, setData] = useState<MeDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | My Dashboard");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await meApi.dashboard());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Your dashboard could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => void load(), [load]);

  const cards = [
    { label: "Check-in", value: data?.check_in_time ? formatTime(data.check_in_time) : "—", icon: LogIn },
    { label: "Check-out", value: data?.check_out_time ? formatTime(data.check_out_time) : "—", icon: LogOut },
    { label: "Working hours", value: `${data?.working_hours ?? 0}h`, icon: Timer },
    { label: "Current shift", value: data?.current_shift?.name ?? "Not assigned", icon: Clock3 },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Personal attendance</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Welcome, {user?.name ?? "User"}</h1>
            <div className="mt-3 flex items-center gap-2 text-sm text-slate-400">
              Today <Badge tone={tone(data?.today_status ?? "not_marked")}>{(data?.today_status ?? "not marked").replace("_", " ")}</Badge>
            </div>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>
            Refresh
          </Button>
        </div>
      </section>

      {error ? <EmptyState title="Dashboard unavailable" description={error} action={<Button onClick={() => void load()}>Try again</Button>} /> : null}
      {!error && !loading && data && !data.employee_linked ? (
        <EmptyState title="Attendance profile not linked" description="Ask your administrator to link your account to your employee record." />
      ) : null}

      {!error && (loading || data?.employee_linked) ? (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map(({ label, value, icon: Icon }) => (
              <Card key={label}>
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm text-slate-500">{label}</p>
                    {loading ? <div className="mt-3 h-8 w-24 animate-pulse rounded-xl bg-slate-100 dark:bg-white/5" /> : <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{value}</p>}
                  </div>
                  <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-500"><Icon className="h-5 w-5" /></div>
                </div>
              </Card>
            ))}
          </section>

          <Card>
            <div className="flex items-center gap-3">
              <CalendarCheck2 className="h-5 w-5 text-cyan-500" />
              <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Monthly summary</h2>
                <p className="text-sm text-slate-500">{data?.monthly_summary.month ?? "Current month"}</p>
              </div>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
              {[
                ["Present", data?.monthly_summary.present ?? 0],
                ["Late", data?.monthly_summary.late ?? 0],
                ["Half day", data?.monthly_summary.half_day ?? 0],
                ["Absent", data?.monthly_summary.absent ?? 0],
                ["Hours", data?.monthly_summary.total_work_hours ?? 0],
                ["Attendance", `${data?.monthly_summary.attendance_percentage ?? 0}%`],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-slate-200 p-4 dark:border-white/10">
                  <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
                  <p className="mt-2 text-xl font-semibold text-slate-900 dark:text-white">{loading ? "…" : value}</p>
                </div>
              ))}
            </div>
          </Card>
        </>
      ) : null}
    </div>
  );
}

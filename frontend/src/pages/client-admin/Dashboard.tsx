import {
  AlertTriangle,
  Camera,
  CameraOff,
  CheckCircle2,
  Clock3,
  RefreshCw,
  UserMinus,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  clientAdminDashboardApi,
  type DashboardRecentActivity,
  type DashboardSummary,
} from "@/services/clientAdminDashboard";
import { formatDate, formatTime } from "@/utils/format";

const initialSummary: DashboardSummary = {
  total_employees: 0,
  active_employees: 0,
  today_present: 0,
  today_absent: 0,
  today_late: 0,
  active_cameras: 0,
  offline_cameras: 0,
  unknown_face_alerts: 0,
};

function confidence(value?: number | null) {
  return value == null ? "-" : `${Math.round(value * 100)}%`;
}

function statusTone(status: string): "success" | "warning" | "danger" | "neutral" {
  if (status === "MATCHED") return "success";
  if (status === "UNKNOWN" || status === "LOW_CONFIDENCE") return "warning";
  if (status.includes("OFFLINE") || status.includes("ERROR")) return "danger";
  return "neutral";
}

export function ClientAdminDashboard() {
  const { currentTenant, hasModule } = useApp();
  const noProductModules = !hasModule("attendance") && !hasModule("object_detection") && !hasModule("visitor_unknown");
  const [summary, setSummary] = useState<DashboardSummary>(initialSummary);
  const [activity, setActivity] = useState<DashboardRecentActivity | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  usePageTitle(`Vision Pass | ${currentTenant?.name ?? "Client Admin"}`);

  const loadDashboard = useCallback(async (refresh = false) => {
    refresh ? setRefreshing(true) : setLoading(true);
    setError(null);
    try {
      const [nextSummary, nextActivity] = await Promise.all([
        clientAdminDashboardApi.getSummary(),
        clientAdminDashboardApi.getRecentActivity(),
      ]);
      setSummary(nextSummary);
      setActivity(nextActivity);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Dashboard data could not be loaded.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const cards = [
    { label: "Total employees", value: summary.total_employees, icon: Users },
    { label: "Active employees", value: summary.active_employees, icon: CheckCircle2 },
    { label: "Today present", value: summary.today_present, icon: CheckCircle2 },
    { label: "Today absent", value: summary.today_absent, icon: UserMinus },
    { label: "Today late", value: summary.today_late, icon: Clock3 },
    { label: "Active cameras", value: summary.active_cameras, icon: Camera },
    { label: "Offline cameras", value: summary.offline_cameras, icon: CameraOff },
    { label: "Unknown face alerts", value: summary.unknown_face_alerts, icon: AlertTriangle },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Badge tone="info">Client admin workspace</Badge>
            <h1 className="mt-2 text-3xl font-semibold text-white">
              {currentTenant?.name ?? "Tenant"} dashboard
            </h1>
            <p className="mt-2 text-sm leading-6 text-slate-400">
              Live employee, attendance, camera, and recognition activity for your tenant.
            </p>
          </div>
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className={`h-4 w-4 ${refreshing ? "animate-spin" : ""}`} />}
            onClick={() => void loadDashboard(true)}
            disabled={loading || refreshing}
          >
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </section>

      {noProductModules ? (
        <EmptyState
          title="No product modules enabled"
          description="Common camera, report, member, and settings tools remain available. Ask your Super Admin to enable Attendance, Visitor + Unknown, or Object Detection."
          action={<Camera className="h-7 w-7 text-slate-400" />}
        />
      ) : error ? (
        <EmptyState
          title="Dashboard unavailable"
          description={error}
          action={<Button onClick={() => void loadDashboard()}>Try again</Button>}
        />
      ) : (
        <>
          <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {cards.map(({ label, value, icon: Icon }) => (
              <Card key={label} className="border-white/10 bg-gradient-to-br from-slate-950/90 to-slate-900/70">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm font-medium text-slate-400">{label}</p>
                    {loading ? (
                      <div className="mt-3 h-9 w-20 animate-pulse rounded-xl bg-white/10" />
                    ) : (
                      <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{value.toLocaleString()}</p>
                    )}
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-300">
                    <Icon className="h-5 w-5" />
                  </div>
                </div>
              </Card>
            ))}
          </section>

          <section className="grid gap-6 xl:grid-cols-2">
            <Card>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent attendance events</h2>
              <p className="mt-1 text-sm text-slate-500">Latest check-ins and check-outs.</p>
              {loading ? (
                <div className="mt-5 grid gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" />)}</div>
              ) : activity?.attendance_events.length ? (
                <div className="mt-5 grid gap-3">
                  {activity.attendance_events.map((event) => (
                    <div key={event.id} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4 dark:border-white/10">
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{event.employee_name}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {event.employee_code} | {event.camera_name ?? event.source} | {formatDate(event.event_time)} {formatTime(event.event_time)}
                        </p>
                      </div>
                      <Badge tone={event.event_type === "check_in" ? "success" : "info"}>{event.event_type.replace("_", " ")}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-5 rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500 dark:border-white/10">
                  No attendance events yet.
                </div>
              )}
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent recognition attempts</h2>
              <p className="mt-1 text-sm text-slate-500">Latest camera recognition results.</p>
              {loading ? (
                <div className="mt-5 grid gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-16 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" />)}</div>
              ) : activity?.recognition_attempts.length ? (
                <div className="mt-5 grid gap-3">
                  {activity.recognition_attempts.map((attempt) => (
                    <div key={attempt.id} className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 p-4 dark:border-white/10">
                      <div>
                        <p className="font-medium text-slate-900 dark:text-white">{attempt.employee_name ?? "Unknown face"}</p>
                        <p className="mt-1 text-xs text-slate-500">
                          {attempt.camera_name} | {confidence(attempt.confidence)} | {formatDate(attempt.created_at)} {formatTime(attempt.created_at)}
                        </p>
                      </div>
                      <Badge tone={statusTone(attempt.recognition_status)}>{attempt.recognition_status.replaceAll("_", " ")}</Badge>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mt-5 rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500 dark:border-white/10">
                  No recognition attempts yet.
                </div>
              )}
            </Card>
          </section>
        </>
      )}
    </div>
  );
}

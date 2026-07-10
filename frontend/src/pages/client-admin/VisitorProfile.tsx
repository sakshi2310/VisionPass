import { ArrowLeft, RefreshCw, Users } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePageTitle } from "@/hooks/usePageTitle";
import { visitorsApi, type VisitorDetail } from "@/services/visitors";
import { formatDate, formatTime } from "@/utils/format";

function tone(status: string): "info" | "success" | "neutral" | "danger" {
  if (status === "expected") return "info";
  if (status === "checked_in") return "success";
  if (status === "blocked") return "danger";
  return "neutral";
}

export function VisitorProfilePage() {
  const { visitorId = "" } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [visitor, setVisitor] = useState<VisitorDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  usePageTitle(`Vision Pass | Visitor Profile`);
  const basePath = location.pathname.startsWith("/tenant-admin") ? "/tenant-admin" : "/client-admin";

  const load = useCallback(async () => {
    if (!visitorId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError("");
    try {
      setVisitor(await visitorsApi.get(visitorId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Visitor profile could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [visitorId]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Visitor profile</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">{visitor?.full_name ?? "Visitor profile"}</h1>
            <p className="mt-2 text-sm text-slate-400">Review the matched visitor record and recent visit history.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" leftIcon={<ArrowLeft className="h-4 w-4" />} onClick={() => navigate(`${basePath}/visitor-unknown/visitors`)}>
              Back to visitors
            </Button>
            <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>
              Refresh
            </Button>
          </div>
        </div>
      </section>

      {error ? (
        <EmptyState title="Visitor profile unavailable" description={error} action={<Button onClick={() => void load()}>Try again</Button>} />
      ) : loading ? (
        <Card className="h-40 animate-pulse bg-slate-100 dark:bg-white/5" />
      ) : visitor ? (
        <>
          <section className="grid gap-4 lg:grid-cols-[0.7fr_1.3fr]">
            <Card>
              <div className="flex items-start gap-4">
                <div className="grid h-16 w-16 place-items-center rounded-3xl bg-cyan-500/10 text-cyan-500">
                  <Users className="h-7 w-7" />
                </div>
                <div>
                  <Badge tone={tone(visitor.status)}>{visitor.status.replaceAll("_", " ")}</Badge>
                  <h2 className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{visitor.full_name}</h2>
                  <p className="mt-1 text-sm text-slate-500">{visitor.company ?? "No company provided"}</p>
                </div>
              </div>
              <div className="mt-6 grid gap-3 text-sm text-slate-600 dark:text-slate-300">
                <p><span className="font-medium">Phone:</span> {visitor.phone}</p>
                <p><span className="font-medium">Email:</span> {visitor.email ?? "N/A"}</p>
                <p><span className="font-medium">Purpose:</span> {visitor.purpose}</p>
                <p><span className="font-medium">Host employee:</span> {visitor.host_employee_id ?? "N/A"}</p>
                <p><span className="font-medium">Photo path:</span> {visitor.photo_path ?? "N/A"}</p>
              </div>
            </Card>

            <Card>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Visits</h2>
              {visitor.visits.length ? (
                <div className="mt-5 grid gap-3">
                  {visitor.visits.map((visit) => (
                    <div key={visit.id} className="rounded-2xl border border-slate-200 p-4 dark:border-white/10">
                      <div className="flex items-center justify-between gap-3">
                        <Badge tone={visit.check_out_time ? "neutral" : "success"}>{visit.check_out_time ? "completed" : "on site"}</Badge>
                        <span className="text-xs text-slate-500">{visit.access_status}</span>
                      </div>
                      <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                        <p>Check-in: {formatDate(visit.check_in_time)} {formatTime(visit.check_in_time)}</p>
                        <p>Check-out: {visit.check_out_time ? `${formatDate(visit.check_out_time)} ${formatTime(visit.check_out_time)}` : "N/A"}</p>
                      </div>
                      {visit.notes ? <p className="mt-3 text-sm text-slate-500">{visit.notes}</p> : null}
                    </div>
                  ))}
                </div>
              ) : (
                <EmptyState title="No visit history" description="This visitor has no recorded visits yet." />
              )}
            </Card>
          </section>
        </>
      ) : null}
    </div>
  );
}

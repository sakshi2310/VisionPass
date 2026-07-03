import { RefreshCw, ShieldAlert, ShieldCheck, ShieldX } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  accessControlApi,
  type AccessDecision,
  type AccessLog,
} from "@/services/accessControl";
import { formatDate, formatTime } from "@/utils/format";

const filters: Array<{ label: string; value?: AccessDecision }> = [
  { label: "All" },
  { label: "Granted", value: "granted" },
  { label: "Denied", value: "denied" },
  { label: "Manual review", value: "manual_review" },
];

function tone(decision: AccessDecision): "success" | "danger" | "warning" {
  if (decision === "granted") return "success";
  if (decision === "denied") return "danger";
  return "warning";
}

function DecisionIcon({ decision }: { decision: AccessDecision }) {
  if (decision === "granted") return <ShieldCheck className="h-5 w-5" />;
  if (decision === "denied") return <ShieldX className="h-5 w-5" />;
  return <ShieldAlert className="h-5 w-5" />;
}

export function AccessControl() {
  const [filter, setFilter] = useState<AccessDecision | undefined>();
  const [logs, setLogs] = useState<AccessLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | Access Logs");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setLogs(await accessControlApi.logs()); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Access logs could not be loaded."); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => void load(), [load]);

  const counts = logs.reduce<Record<AccessDecision, number>>(
    (current, log) => ({ ...current, [log.decision]: current[log.decision] + 1 }),
    { granted: 0, denied: 0, manual_review: 0 },
  );
  const visibleLogs = filter ? logs.filter((log) => log.decision === filter) : logs;

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Access control</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Access decision logs</h1>
            <p className="mt-2 text-sm text-slate-400">Review granted, denied, and manual-review decisions for your tenant.</p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>Refresh</Button>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {([
          ["Granted", counts.granted, "granted"],
          ["Denied", counts.denied, "denied"],
          ["Manual review", counts.manual_review, "manual_review"],
        ] as const).map(([label, value, decision]) => (
          <Card key={decision} className="flex items-center justify-between">
            <div><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "…" : value}</p></div>
            <div className={`rounded-2xl p-3 ${decision === "granted" ? "bg-emerald-500/10 text-emerald-500" : decision === "denied" ? "bg-rose-500/10 text-rose-500" : "bg-amber-500/10 text-amber-500"}`}><DecisionIcon decision={decision} /></div>
          </Card>
        ))}
      </section>

      <div className="flex flex-wrap gap-2">
        {filters.map((item) => <Button key={item.label} size="sm" variant={filter === item.value ? "primary" : "secondary"} onClick={() => setFilter(item.value)}>{item.label}</Button>)}
      </div>

      {error ? <EmptyState title="Access logs unavailable" description={error} action={<Button onClick={() => void load()}>Try again</Button>} /> : loading ? (
        <Card><div className="grid gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-20 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" />)}</div></Card>
      ) : visibleLogs.length ? (
        <Card>
          <div className="mb-5"><h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent access activity</h2><p className="text-sm text-slate-500">Newest decisions appear first.</p></div>
          <div className="grid gap-3">
            {visibleLogs.map((log) => (
              <div key={log.id} className="flex flex-col gap-4 rounded-2xl border border-slate-200 p-4 sm:flex-row sm:items-center sm:justify-between dark:border-white/10">
                <div className="flex items-start gap-3">
                  <div className={`rounded-2xl p-3 ${log.decision === "granted" ? "bg-emerald-500/10 text-emerald-500" : log.decision === "denied" ? "bg-rose-500/10 text-rose-500" : "bg-amber-500/10 text-amber-500"}`}><DecisionIcon decision={log.decision} /></div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2"><p className="font-semibold text-slate-900 dark:text-white">{log.identity_name ?? "Unresolved identity"}</p><Badge tone={tone(log.decision)}>{log.decision.replace("_", " ")}</Badge></div>
                    <p className="mt-1 text-sm text-slate-500">{log.reason.replaceAll("_", " ")} · {log.camera_name ?? "No camera"}</p>
                    <p className="mt-1 text-xs text-slate-400">{formatDate(log.created_at)} {formatTime(log.created_at)}</p>
                  </div>
                </div>
                <div className="text-sm text-slate-500">{log.confidence == null ? "No confidence" : `${Math.round(log.confidence * 100)}% confidence`}</div>
              </div>
            ))}
          </div>
        </Card>
      ) : <EmptyState title="No access decisions" description="No access activity matches the selected filter." />}
    </div>
  );
}

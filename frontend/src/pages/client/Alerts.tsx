import { CheckCircle2, Eye, Flame, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  alertsApi,
  type Alert,
  type AlertStatus,
} from "@/services/alerts";
import { formatDate, formatTime } from "@/utils/format";

const filters: Array<{ label: string; value?: AlertStatus }> = [
  { label: "All" },
  { label: "Open", value: "open" },
  { label: "Acknowledged", value: "acknowledged" },
  { label: "Resolved", value: "resolved" },
];

export function Alerts() {
  const [filter, setFilter] = useState<AlertStatus | undefined>();
  const [items, setItems] = useState<Alert[]>([]);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | Alerts");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setItems(await alertsApi.list(filter)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Alerts could not be loaded."); }
    finally { setLoading(false); }
  }, [filter]);
  useEffect(() => void load(), [load]);

  async function changeStatus(alert: Alert, action: "acknowledge" | "resolve") {
    setBusy(alert.id);
    setError("");
    try {
      const updated = action === "acknowledge"
        ? await alertsApi.acknowledge(alert.id)
        : await alertsApi.resolve(alert.id);
      setItems((current) => current.map((item) => item.id === updated.id ? updated : item));
      if (selected?.id === updated.id) setSelected(updated);
      if (filter && updated.status !== filter) await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Alert could not be updated.");
    } finally {
      setBusy("");
    }
  }

  async function openDetail(alert: Alert) {
    setBusy(alert.id);
    try { setSelected(await alertsApi.get(alert.id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Alert detail could not be loaded."); }
    finally { setBusy(""); }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Alerts</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Security and attendance alerts</h1>
            <p className="mt-2 text-sm text-slate-400">Review important events and track them through acknowledgement and resolution.</p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>Refresh</Button>
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        {filters.map((item) => <Button key={item.label} size="sm" variant={filter === item.value ? "primary" : "secondary"} onClick={() => setFilter(item.value)}>{item.label}</Button>)}
      </div>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600">{error}</div> : null}

      {loading ? <Card><div className="grid gap-3">{[1, 2, 3].map((item) => <div key={item} className="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" />)}</div></Card> : items.length ? (
        <div className="grid gap-4 xl:grid-cols-2">
          {items.map((alert) => (
            <Card key={alert.id} className="grid gap-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="rounded-2xl bg-rose-500/10 p-3 text-rose-500"><Flame className="h-5 w-5" /></div>
                  <div>
                    <div className="flex flex-wrap items-center gap-2"><h2 className="font-semibold text-slate-900 dark:text-white">{alert.title}</h2><Badge tone={alert.severity}>{alert.severity}</Badge></div>
                    <p className="mt-1 text-xs text-slate-500">{alert.alert_type.replaceAll("_", " ")} · {formatDate(alert.created_at)} {formatTime(alert.created_at)}</p>
                  </div>
                </div>
                <Badge tone={alert.status === "resolved" ? "success" : alert.status === "acknowledged" ? "info" : "warning"}>{alert.status}</Badge>
              </div>
              <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{alert.message}</p>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" leftIcon={<Eye className="h-4 w-4" />} onClick={() => void openDetail(alert)}>Detail</Button>
                {alert.status === "open" ? <Button size="sm" variant="secondary" onClick={() => void changeStatus(alert, "acknowledge")} disabled={busy === alert.id}>Acknowledge</Button> : null}
                {alert.status !== "resolved" ? <Button size="sm" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => void changeStatus(alert, "resolve")} disabled={busy === alert.id}>Resolve</Button> : null}
              </div>
            </Card>
          ))}
        </div>
      ) : <EmptyState title="No alerts found" description="No alerts match the selected status." />}

      <Modal open={Boolean(selected)} title={selected?.title ?? "Alert detail"} onClose={() => setSelected(null)}>
        {selected ? <div className="grid gap-4">
          <div className="flex flex-wrap gap-2"><Badge tone={selected.severity}>{selected.severity}</Badge><Badge tone={selected.status === "resolved" ? "success" : selected.status === "acknowledged" ? "info" : "warning"}>{selected.status}</Badge><Badge tone="neutral">{selected.alert_type}</Badge></div>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{selected.message}</p>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 p-4 dark:border-white/10"><p className="text-xs uppercase text-slate-500">Source</p><p className="mt-2 text-sm">{selected.source_type} · {selected.source_id ?? "—"}</p></div>
            <div className="rounded-2xl border border-slate-200 p-4 dark:border-white/10"><p className="text-xs uppercase text-slate-500">Created</p><p className="mt-2 text-sm">{formatDate(selected.created_at)} {formatTime(selected.created_at)}</p></div>
          </div>
          <div className="rounded-2xl border border-slate-200 p-4 dark:border-white/10"><p className="text-xs uppercase text-slate-500">Metadata</p><pre className="mt-3 overflow-x-auto whitespace-pre-wrap text-xs text-slate-600 dark:text-slate-300">{JSON.stringify(selected.metadata, null, 2)}</pre></div>
          <div className="flex gap-2">
            {selected.status === "open" ? <Button variant="secondary" onClick={() => void changeStatus(selected, "acknowledge")}>Acknowledge</Button> : null}
            {selected.status !== "resolved" ? <Button onClick={() => void changeStatus(selected, "resolve")}>Resolve</Button> : null}
          </div>
        </div> : null}
      </Modal>
    </div>
  );
}

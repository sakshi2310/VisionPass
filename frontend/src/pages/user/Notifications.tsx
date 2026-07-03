import { Bell, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePageTitle } from "@/hooks/usePageTitle";
import { meApi, type MeNotification } from "@/services/me";
import { formatDate, formatTime } from "@/utils/format";

export function TenantUserNotifications() {
  const [items, setItems] = useState<MeNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | Notifications");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setItems(await meApi.notifications()); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Notifications could not be loaded."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => void load(), [load]);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex items-end justify-between gap-4">
          <div><p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Notifications</p><h1 className="mt-2 text-3xl font-semibold text-white">My attendance updates</h1></div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>Refresh</Button>
        </div>
      </section>
      {error ? <EmptyState title="Notifications unavailable" description={error} /> : loading ? <Card><div className="h-20 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" /></Card> : items.length ? (
        <div className="grid gap-3">
          {items.map((item) => (
            <Card key={item.id} className="flex items-start gap-4">
              <div className="rounded-2xl bg-amber-500/10 p-3 text-amber-500"><Bell className="h-5 w-5" /></div>
              <div className="flex-1"><div className="flex items-center gap-2"><h2 className="font-semibold text-slate-900 dark:text-white">{item.title}</h2><Badge tone={item.severity === "warning" ? "warning" : "info"}>{item.type}</Badge></div><p className="mt-2 text-sm text-slate-500">{item.message}</p><p className="mt-2 text-xs text-slate-400">{formatDate(item.created_at)} {formatTime(item.created_at)}</p></div>
            </Card>
          ))}
        </div>
      ) : <EmptyState title="You're all caught up" description="No personal attendance notifications are available." />}
    </div>
  );
}

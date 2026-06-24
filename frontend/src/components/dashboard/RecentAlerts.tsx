import { AlertTriangle } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { formatTime } from "@/utils/format";
import type { AlertItem } from "@/types";

export function RecentAlerts({ alerts }: { alerts: AlertItem[] }) {
  return (
    <Card className="grid gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-base font-semibold">Recent Alerts</h3>
        <Badge tone="info">{alerts.length} active</Badge>
      </div>
      <div className="grid gap-3">
        {alerts.slice(0, 4).map((alert) => (
          <div
            key={alert.id}
            className="flex items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-white/10 dark:bg-slate-950/30"
          >
            <div className="rounded-2xl bg-rose-500/10 p-2 text-rose-500">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-medium">{alert.title}</p>
                <Badge tone={alert.severity}>{alert.severity}</Badge>
              </div>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{alert.detail}</p>
            </div>
            <span className="text-xs text-slate-500 dark:text-slate-400">{formatTime(alert.time)}</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

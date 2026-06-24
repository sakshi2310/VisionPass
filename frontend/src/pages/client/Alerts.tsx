import { CheckCircle2, Flame, MessageSquareWarning } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { alerts as alertSeed } from "@/data/mockData";

export function Alerts() {
  const [items, setItems] = useState(alertSeed);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Alerts</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Security alerts and notifications</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Track severities from low to critical, resolve incidents, and keep a clear audit trail.
        </p>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        {items.map((alert) => (
          <Card key={alert.id} className="grid gap-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl bg-rose-500/10 p-3 text-rose-400">
                  <Flame className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{alert.title}</h3>
                    <Badge tone={alert.severity}>{alert.severity}</Badge>
                  </div>
                  <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {alert.category} · {alert.time}
                  </div>
                </div>
              </div>
              <Badge tone={alert.resolved ? "success" : "warning"}>{alert.resolved ? "resolved" : "open"}</Badge>
            </div>
            <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{alert.detail}</p>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                leftIcon={<CheckCircle2 className="h-4 w-4" />}
                onClick={() => setItems((current) => current.map((item) => (item.id === alert.id ? { ...item, resolved: true } : item)))}
              >
                Mark resolved
              </Button>
              <Button variant="secondary" leftIcon={<MessageSquareWarning className="h-4 w-4" />}>
                Add note
              </Button>
            </div>
          </Card>
        ))}
      </section>
    </div>
  );
}

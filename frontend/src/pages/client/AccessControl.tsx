import { ShieldCheck, ShieldOff, Unlock, WandSparkles } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { accessEvents } from "@/data/mockData";

export function AccessControl() {
  const [items, setItems] = useState(accessEvents);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Access control</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Access decision logs</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Review allowed and denied gate events, inspect reasons, and use manual override when escalation is needed.
        </p>
      </section>

      <div className="grid gap-4">
        {items.map((event) => (
          <Card key={event.id} className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">
            <div className="grid gap-2">
              <div className="flex flex-wrap items-center gap-2">
                <h3 className="text-lg font-semibold text-slate-900 dark:text-white">{event.identity}</h3>
                <Badge tone={event.status === "allowed" ? "success" : "danger"}>{event.status}</Badge>
              </div>
              <div className="text-sm text-slate-500 dark:text-slate-400">
                {event.gate} · {event.timestamp} · {event.confidence}% confidence
              </div>
              <p className="max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{event.reason}</p>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button
                variant="secondary"
                leftIcon={event.status === "allowed" ? <Unlock className="h-4 w-4" /> : <ShieldCheck className="h-4 w-4" />}
              >
                {event.status === "allowed" ? "Approved" : "Denied"}
              </Button>
              <Button
                variant="secondary"
                leftIcon={<WandSparkles className="h-4 w-4" />}
                onClick={() =>
                  setItems((current) =>
                    current.map((item) => (item.id === event.id ? { ...item, status: "allowed" } : item)),
                  )
                }
              >
                Manual override
              </Button>
              <Button variant="secondary" leftIcon={<ShieldOff className="h-4 w-4" />}>
                Escalate
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

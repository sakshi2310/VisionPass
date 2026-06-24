import { AlertTriangle, CheckCircle2, EyeOff, UserRoundSearch } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { visitorLogs } from "@/data/mockData";
import { formatPercentage } from "@/utils/format";

export function Visitors() {
  const [items, setItems] = useState(visitorLogs);

  function markKnown(id: string) {
    setItems((current) =>
      current.map((item) => (item.id === id ? { ...item, classification: "staff" as const } : item)),
    );
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Visitors</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Unknown visitor logs</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Review unidentified visitors, compare confidence scores, and decide whether to mark known, alert security,
          or ignore the event.
        </p>
      </section>

      <section className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
        {items.map((visitor) => (
          <Card key={visitor.id} className="grid gap-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="grid h-14 w-14 place-items-center rounded-2xl border border-white/10 bg-gradient-to-br from-brand-500/30 to-cyan-400/30 text-sm font-semibold text-white">
                  {visitor.thumbnail}
                </div>
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{visitor.name}</div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">{visitor.camera}</div>
                </div>
              </div>
              <Badge tone={visitor.classification === "unknown" ? "warning" : "success"}>{visitor.classification}</Badge>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-3">
                <div className="text-slate-500 dark:text-slate-400">Confidence</div>
                <div className="mt-1 text-lg font-semibold text-white">{formatPercentage(visitor.confidence)}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-3">
                <div className="text-slate-500 dark:text-slate-400">First seen</div>
                <div className="mt-1 text-lg font-semibold text-white">{visitor.firstSeen}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-3">
                <div className="text-slate-500 dark:text-slate-400">Last seen</div>
                <div className="mt-1 text-lg font-semibold text-white">{visitor.lastSeen}</div>
              </div>
              <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-3">
                <div className="text-slate-500 dark:text-slate-400">Identity</div>
                <div className="mt-1 text-lg font-semibold text-white">{visitor.classification}</div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button variant="secondary" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => markKnown(visitor.id)}>
                Mark as known
              </Button>
              <Button variant="secondary" leftIcon={<AlertTriangle className="h-4 w-4" />}>
                Alert
              </Button>
              <Button variant="secondary" leftIcon={<EyeOff className="h-4 w-4" />}>
                Ignore
              </Button>
            </div>
          </Card>
        ))}
      </section>

      <Card className="grid gap-3">
        <div className="flex items-center gap-3">
          <UserRoundSearch className="h-5 w-5 text-cyan-400" />
          <h3 className="text-base font-semibold">Classification summary</h3>
        </div>
        <div className="grid gap-3 md:grid-cols-3">
          {[
            { label: "Unknown", value: "2 logs" },
            { label: "Staff matched", value: "1 log" },
            { label: "Vendor verified", value: "1 log" },
          ].map((item) => (
            <div key={item.label} className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">{item.label}</div>
              <div className="mt-1 text-2xl font-semibold text-white">{item.value}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

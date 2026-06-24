import { ArrowUpRight } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { cn } from "@/utils/cn";
import type { StatDefinition } from "@/types";

const toneClasses: Record<StatDefinition["tone"], string> = {
  brand: "from-brand-500/20 to-brand-500/5 text-brand-600 dark:text-brand-300",
  emerald: "from-emerald-500/20 to-emerald-500/5 text-emerald-600 dark:text-emerald-300",
  amber: "from-amber-500/20 to-amber-500/5 text-amber-600 dark:text-amber-300",
  rose: "from-rose-500/20 to-rose-500/5 text-rose-600 dark:text-rose-300",
};

export function StatCard({ label, value, delta, tone }: StatDefinition) {
  return (
    <Card className={cn("relative overflow-hidden border-white/10 bg-gradient-to-br", toneClasses[tone])}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</p>
          <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">{value}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/70 p-2 text-slate-900 dark:bg-slate-950/70 dark:text-white">
          <ArrowUpRight className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">{delta}</p>
    </Card>
  );
}

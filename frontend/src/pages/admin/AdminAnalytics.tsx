import { ResponsiveContainer, LineChart, Line, CartesianGrid, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { Card } from "@/components/ui/Card";
import { systemUsage } from "@/data/mockData";
import { usePageTitle } from "@/hooks/usePageTitle";

const adoption = [
  { name: "Attendance", value: 92 },
  { name: "Visitors", value: 84 },
  { name: "Access", value: 78 },
  { name: "Alerts", value: 88 },
  { name: "Assistant", value: 71 },
  { name: "Analytics", value: 95 },
];

export function AdminAnalytics() {
  usePageTitle("VisionPass AI | Analytics");

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Platform analytics</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Cross-tenant analytics</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Track platform usage, adoption, and system health across the full VisionPass AI installation.
        </p>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <ChartCard title="Feature adoption" description="How widely each module is enabled across tenants.">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={adoption}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="System usage" description="Infrastructure and event throughput telemetry.">
          <div className="grid gap-3">
            {systemUsage.map((item) => (
              <div key={item.name} className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm text-slate-500 dark:text-slate-400">{item.name}</div>
                    <div className="mt-1 text-xl font-semibold text-white">{item.value}%</div>
                  </div>
                  <div className="h-2 flex-1 rounded-full bg-white/10">
                    <div className="h-2 rounded-full bg-gradient-to-r from-brand-500 to-cyan-400" style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </section>

      <Card className="grid gap-4">
        <h3 className="text-base font-semibold">Operator notes</h3>
        <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
          This page is intentionally lightweight but ready to accept live backend metrics for queue depth, camera
          throughput, AI inference latency, and tenant health scoring.
        </p>
      </Card>
    </div>
  );
}

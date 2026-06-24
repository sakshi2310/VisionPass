import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { StatCard } from "@/components/dashboard/StatCard";
import { analyticsSeries } from "@/data/mockData";

const moduleColors = ["#38bdf8", "#22c55e", "#f59e0b", "#f43f5e", "#a855f7", "#14b8a6", "#60a5fa"];

export function Analytics() {
  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Analytics</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Platform analytics</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Combine attendance, visitors, alerts, and module usage into one operational view.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Attendance growth", value: "+12%", delta: "vs last month", tone: "brand" as const },
          { label: "Unknown visitors", value: "17", delta: "current week", tone: "amber" as const },
          { label: "Resolved alerts", value: "28", delta: "this month", tone: "emerald" as const },
          { label: "Module adoption", value: "84%", delta: "enabled footprint", tone: "rose" as const },
        ].map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <ChartCard title="Attendance over time" description="Weekly attendance volumes across the selected tenant.">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={analyticsSeries.attendance}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#22d3ee" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Unknown visitor count" description="Weekly unknown-person detections.">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={analyticsSeries.unknownVisitors}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="value" radius={[12, 12, 0, 0]} fill="#f59e0b" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Alerts by severity" description="Distribution of incidents over the current cycle.">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={analyticsSeries.alertSeverity}
                dataKey="value"
                nameKey="name"
                innerRadius={62}
                outerRadius={100}
                paddingAngle={4}
              >
                {analyticsSeries.alertSeverity.map((entry, index) => (
                  <Cell key={entry.name} fill={moduleColors[index % moduleColors.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Module usage" description="How heavily each module is exercised by the current tenant.">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={analyticsSeries.moduleUsage} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis type="number" stroke="#94a3b8" />
              <YAxis dataKey="name" type="category" width={110} stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#38bdf8" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </section>
    </div>
  );
}

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChartCard } from "@/components/dashboard/ChartCard";
import { RecentAlerts } from "@/components/dashboard/RecentAlerts";
import { StatCard } from "@/components/dashboard/StatCard";
import { AttendanceTable } from "@/components/dashboard/AttendanceTable";
import { Badge } from "@/components/ui/Badge";
import { useApp } from "@/context/AppContext";
import { attendanceRows, attendanceTrend, dashboardStats, alerts } from "@/data/mockData";

export function ClientDashboard() {
  const { currentTenant } = useApp();

  return (
    <div className="grid gap-6">
      <section className="space-y-2">
        <Badge tone="info">Client workspace</Badge>
        <h1 className="text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
          {currentTenant?.name ?? "Tenant"} dashboard
        </h1>
        <p className="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-400">
          Tenant-scoped attendance, visitor, access, and alert activity in one place.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {dashboardStats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <ChartCard
          title="Attendance trend"
          description="Daily check-ins versus late arrivals."
          className="min-h-[380px]"
        >
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={attendanceTrend}>
              <defs>
                <linearGradient id="attendanceFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22d3ee" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#22d3ee" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Area type="monotone" dataKey="checkedIn" stroke="#22d3ee" fill="url(#attendanceFill)" strokeWidth={3} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>

        <RecentAlerts alerts={alerts} />
      </section>

      <section className="grid gap-6">
        <AttendanceTable rows={attendanceRows.slice(0, 4)} />
      </section>
    </div>
  );
}

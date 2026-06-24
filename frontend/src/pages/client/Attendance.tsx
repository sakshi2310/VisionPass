import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Calendar, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { AttendanceTable } from "@/components/dashboard/AttendanceTable";
import { ChartCard } from "@/components/dashboard/ChartCard";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { attendanceRows } from "@/data/mockData";

export function Attendance() {
  const [date, setDate] = useState("");
  const [status, setStatus] = useState("all");
  const [search, setSearch] = useState("");

  const filteredRows = useMemo(() => {
    return attendanceRows.filter((row) => {
      const matchesDate = !date || row.date === date;
      const matchesStatus = status === "all" || row.status === status;
      const matchesSearch =
        !search ||
        [row.employee, row.camera, row.action].join(" ").toLowerCase().includes(search.toLowerCase());
      return matchesDate && matchesStatus && matchesSearch;
    });
  }, [date, search, status]);

  const weeklyData = [
    { name: "Mon", present: 180, late: 7 },
    { name: "Tue", present: 186, late: 5 },
    { name: "Wed", present: 192, late: 4 },
    { name: "Thu", present: 179, late: 8 },
    { name: "Fri", present: 195, late: 3 },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Attendance</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Employee attendance records</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Search attendance events by date, status, or camera to quickly review check-in patterns and confidence
              scores.
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <Input label="Date" type="date" value={date} onChange={(event) => setDate(event.target.value)} leftIcon={<Calendar className="h-4 w-4" />} />
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-300">Status</span>
              <select
                value={status}
                onChange={(event) => setStatus(event.target.value)}
                className="h-11 rounded-2xl border border-white/10 bg-white/80 px-4 text-slate-900 outline-none dark:bg-slate-950/70 dark:text-white"
              >
                <option value="all">All</option>
                <option value="checked_in">Checked in</option>
                <option value="late">Late</option>
                <option value="manual">Manual</option>
                <option value="absent">Absent</option>
              </select>
            </label>
            <Input label="Search" value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="h-4 w-4" />} />
          </div>
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <AttendanceTable rows={filteredRows} />
        <ChartCard title="Daily / weekly attendance" description="Attendance and late arrivals for the last working week.">
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={weeklyData}>
              <defs>
                <linearGradient id="weeklyFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#22c55e" stopOpacity={0.38} />
                  <stop offset="95%" stopColor="#22c55e" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="name" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Area type="monotone" dataKey="present" stroke="#22c55e" fill="url(#weeklyFill)" strokeWidth={3} />
            </AreaChart>
          </ResponsiveContainer>
          <Button className="mt-4 w-full" variant="secondary">
            Export CSV
          </Button>
        </ChartCard>
      </section>
    </div>
  );
}

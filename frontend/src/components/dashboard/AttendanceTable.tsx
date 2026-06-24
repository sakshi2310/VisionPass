import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/ui/DataTable";
import { formatPercentage } from "@/utils/format";
import type { AttendanceRecord } from "@/types";

const toneMap = {
  checked_in: "success",
  late: "warning",
  absent: "danger",
  manual: "info",
} as const;

export function AttendanceTable({ rows }: { rows: AttendanceRecord[] }) {
  return (
    <DataTable headers={["Employee", "Time", "Status", "Confidence", "Camera", "Action"]}>
      {rows.map((row) => (
        <tr key={row.id} className="hover:bg-slate-50 dark:hover:bg-white/5">
          <td className="px-5 py-4">
            <div className="font-medium text-slate-900 dark:text-white">{row.employee}</div>
            <div className="text-sm text-slate-500 dark:text-slate-400">{row.date}</div>
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{row.time}</td>
          <td className="px-5 py-4">
            <Badge tone={toneMap[row.status]}>{row.status.replace("_", " ")}</Badge>
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
            {formatPercentage(row.confidence)}
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{row.camera}</td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{row.action}</td>
        </tr>
      ))}
    </DataTable>
  );
}

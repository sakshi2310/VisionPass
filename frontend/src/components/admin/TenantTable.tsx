import { Badge } from "@/components/ui/Badge";
import { DataTable } from "@/components/ui/DataTable";
import { formatPercentage } from "@/utils/format";
import type { Tenant } from "@/types";
import { Building2, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";

const statusTone = {
  active: "success",
  trial: "warning",
  paused: "danger",
} as const;

export function TenantTable({ tenants }: { tenants: Tenant[] }) {
  return (
    <DataTable headers={["Tenant", "Plan", "Status", "Modules", "Users", "Actions"]}>
      {tenants.map((tenant) => (
        <tr key={tenant.id} className="hover:bg-white/5">
          <td className="px-5 py-4">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-brand-500/10 p-3 text-brand-500">
                <Building2 className="h-4 w-4" />
              </div>
              <div>
                <div className="font-medium">{tenant.name}</div>
                <div className="text-sm text-slate-500 dark:text-slate-400">{tenant.code}</div>
              </div>
            </div>
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{tenant.plan}</td>
          <td className="px-5 py-4">
            <Badge tone={statusTone[tenant.status]}>{tenant.status}</Badge>
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
            {tenant.enabledModules.length} enabled
          </td>
          <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
            {formatPercentage((tenant.users / 650) * 100)}
          </td>
          <td className="px-5 py-4">
            <Link
              to={`/admin/tenants/${tenant.id}`}
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-white/5 hover:text-slate-900 dark:text-slate-200 dark:hover:text-white"
            >
              <ExternalLink className="h-4 w-4" />
              View
            </Link>
          </td>
        </tr>
      ))}
    </DataTable>
  );
}

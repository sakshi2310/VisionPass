import { ShieldCheck, UserRound } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";

export function TenantAdminSettings() {
  const { user, currentTenant } = useApp();

  usePageTitle("Vision Pass | Tenant Settings");

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Tenant settings</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Workspace settings</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          This area is intentionally limited. Tenant admins can review scope and account context, but cannot create tenants from this workspace.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400">
              <ShieldCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Access level</div>
              <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">Tenant Admin</div>
            </div>
          </div>
          <div className="mt-4">
            <Badge tone="info">Tenant scoped</Badge>
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400">
              <UserRound className="h-5 w-5" />
            </div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Signed in as</div>
              <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">{user?.name ?? "Tenant admin"}</div>
            </div>
          </div>
          <div className="mt-4 text-sm text-slate-500 dark:text-slate-400">{user?.email ?? "-"}</div>
        </Card>

        <Card className="p-5">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tenant</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{currentTenant?.name ?? "Current tenant"}</div>
          <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">Tenant ID: {currentTenant?.id ?? user?.tenantId ?? "-"}</div>
        </Card>
      </div>

      <Card className="grid gap-3 p-5">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Guardrails</h2>
        <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
          The backend blocks access unless the logged-in account is a tenant member with the tenant_admin role. All data shown in this workspace is filtered by the current tenant_id.
        </p>
        <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
          Tenant admins can manage members and review enabled features, but cannot create, move, or inspect other tenants.
        </p>
      </Card>
    </div>
  );
}

import { ExternalLink, LayoutDashboard, RefreshCw, ShieldCheck, Sparkles, UserCircle2 } from "lucide-react";
import { Link } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getUserWorkspaceDashboard, type UserWorkspaceDashboard } from "@/services/userWorkspace";

function statusTone(status: string) {
  if (status === "active") return "success" as const;
  if (status === "suspended") return "warning" as const;
  return "danger" as const;
}

export function TenantUserDashboard() {
  const { currentTenant, user } = useApp();
  const [dashboard, setDashboard] = useState<UserWorkspaceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  usePageTitle("VisionPass AI | User Dashboard");

  async function loadDashboard() {
    try {
      setError("");
      setRefreshing(true);
      setDashboard(await getUserWorkspaceDashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load your workspace.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const features = dashboard?.features ?? [];
  const openableFeatures = useMemo(() => features.filter((feature) => feature.route), [features]);

  const cards = [
    { label: "Assigned Features", value: dashboard?.summary.assigned_features_count ?? 0, icon: Sparkles },
    { label: "Open Modules", value: dashboard?.summary.open_modules_count ?? 0, icon: LayoutDashboard },
    { label: "Profile Status", value: user?.isActive ? 1 : 0, icon: ShieldCheck },
    { label: "Tenant Scope", value: currentTenant?.name ? 1 : 0, icon: UserCircle2 },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">User dashboard</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Welcome, {user?.name ?? dashboard?.summary.member_name ?? "User"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Your workspace is filtered by tenant and member identity. You only see features assigned to your account.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadDashboard()} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Card key={card.label} className="border-white/10 bg-gradient-to-br from-slate-950/90 to-slate-900/70">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-400">{card.label}</p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{loading ? "..." : card.value}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            </Card>
          );
        })}
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">My Features</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">Open only the modules assigned to your account.</p>
            </div>
            <Badge tone="info">{features.length} assigned</Badge>
          </div>

          <div className="grid gap-3">
            {features.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                No features are assigned to your account yet.
              </div>
            ) : (
              features.map((feature) => (
                <div key={feature.feature_code} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{feature.feature_code}</div>
                      {feature.description ? <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">{feature.description}</p> : null}
                    </div>
                    {feature.route ? (
                      <Link to={feature.route} className="inline-flex">
                        <Button size="sm" rightIcon={<ExternalLink className="h-4 w-4" />}>Open</Button>
                      </Link>
                    ) : (
                      <Badge tone="neutral">No route</Badge>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Workspace Scope</h2>
          <div className="grid gap-3 text-sm text-slate-600 dark:text-slate-300">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Tenant: {dashboard?.summary.tenant_name ?? currentTenant?.name ?? "-"}
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Member ID: {dashboard?.summary.member_id ?? user?.id ?? "-"}
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Role: {dashboard?.summary.member_role ?? user?.role ?? "user"}
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Open modules available: {openableFeatures.length}
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

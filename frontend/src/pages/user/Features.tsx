import { ExternalLink } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getUserWorkspaceDashboard, type UserWorkspaceDashboard } from "@/services/userWorkspace";

export function TenantUserFeatures() {
  const { currentTenant } = useApp();
  const [dashboard, setDashboard] = useState<UserWorkspaceDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  usePageTitle("Vision Pass | My Features");

  async function loadFeatures() {
    try {
      setError("");
      setRefreshing(true);
      setDashboard(await getUserWorkspaceDashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load your features.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadFeatures();
  }, []);

  const features = dashboard?.features ?? [];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">My features</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Features for {currentTenant?.name ?? "your tenant"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This list is scoped to your member account. Only assigned features with open routes can be launched from here.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<ExternalLink className="h-4 w-4" />} onClick={() => void loadFeatures()} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </section>

      <Card className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Assigned modules</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">Only your account's enabled features appear here.</p>
          </div>
          <Badge tone="info">{features.length} features</Badge>
        </div>
      </Card>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <DataTable
        title="My Feature List"
        subtitle="Feature Name, Code, Route, Action"
        headers={["Feature Name", "Code", "Route", "Action"]}
        emptyState={
          !loading && features.length === 0 ? (
            <div className="px-5 py-10 text-center text-sm text-slate-500 dark:text-slate-400">No features are assigned to your account yet.</div>
          ) : null
        }
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={4}>
              Loading features...
            </td>
          </tr>
        ) : (
          features.map((feature) => (
            <tr key={feature.feature_code}>
              <td className="px-5 py-4">
                <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                {feature.description ? <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{feature.description}</div> : null}
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{feature.feature_code}</td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{feature.route ?? "-"}</td>
              <td className="px-5 py-4">
                {feature.route ? (
                  <Link to={feature.route} className="inline-flex">
                    <Button size="sm">Open</Button>
                  </Link>
                ) : (
                  <Badge tone="neutral">Locked</Badge>
                )}
              </td>
            </tr>
          ))
        )}
      </DataTable>
    </div>
  );
}

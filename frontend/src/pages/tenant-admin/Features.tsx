import { RefreshCw, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { tenantAdminApi, type TenantAdminFeature } from "@/services/tenantAdmin";

function featureCodeLabel(code: string) {
  return code.replace(/_/g, " ").toUpperCase();
}

export function TenantAdminFeatures() {
  const { currentTenant } = useApp();
  const [features, setFeatures] = useState<TenantAdminFeature[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");

  usePageTitle("VisionPass AI | Tenant Features");

  async function loadFeatures() {
    try {
      setError("");
      setRefreshing(true);
      setFeatures(await tenantAdminApi.listFeatures());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load features.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadFeatures();
  }, []);

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Tenant features</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Enabled features for {currentTenant?.name ?? "your tenant"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This page only lists the features already enabled for the logged-in tenant. Tenant admins cannot create platform-wide features here.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadFeatures()} disabled={refreshing}>
            {refreshing ? "Refreshing..." : "Refresh"}
          </Button>
        </div>
      </section>

      <Card className="p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Feature list</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">Assigned features visible to this tenant.</p>
          </div>
          <Badge tone="info">{features.length} enabled</Badge>
        </div>
      </Card>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <DataTable
        title="Tenant feature assignments"
        subtitle="Feature Name, Code, Description"
        headers={["Feature Name", "Code", "Description"]}
        emptyState={
          !loading && features.length === 0 ? (
            <div className="px-5 py-10 text-center text-sm text-slate-500 dark:text-slate-400">No enabled features found for this tenant.</div>
          ) : null
        }
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={3}>
              Loading features...
            </td>
          </tr>
        ) : (
          features.map((feature) => (
            <tr key={feature.feature_code}>
              <td className="px-5 py-4">
                <div className="flex items-center gap-3">
                  <span className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-2 text-cyan-500">
                    <Sparkles className="h-4 w-4" />
                  </span>
                  <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                </div>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                <Badge tone="neutral">{featureCodeLabel(feature.feature_code)}</Badge>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{feature.description ?? "-"}</td>
            </tr>
          ))
        )}
      </DataTable>
    </div>
  );
}

import { Building2, RefreshCw, Sparkles, Users } from 'lucide-react';
import { useEffect, useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { useApp } from '@/context/AppContext';
import { tenantAdminApi, type TenantAdminDashboardSummary, type TenantAdminFeature } from '@/services/tenantAdmin';
import { usePageTitle } from '@/hooks/usePageTitle';

function CountUp({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const duration = 650;
    const start = performance.now();

    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      setDisplayValue(Math.round(value * progress));
      if (progress < 1) frame = window.requestAnimationFrame(animate);
    };

    frame = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frame);
  }, [value]);

  return <span>{displayValue.toLocaleString()}</span>;
}

export function TenantAdminDashboard() {
  const { currentTenant, user } = useApp();
  const [summary, setSummary] = useState<TenantAdminDashboardSummary | null>(null);
  const [features, setFeatures] = useState<TenantAdminFeature[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  usePageTitle('Vision Pass | ' + (currentTenant?.name ?? 'Tenant Admin'));

  async function loadDashboard() {
    try {
      setRefreshing(true);
      const [summaryResponse, featureResponse] = await Promise.all([tenantAdminApi.getDashboardSummary(), tenantAdminApi.listFeatures()]);
      setSummary(summaryResponse);
      setFeatures(featureResponse);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const cards = [
    { label: 'Total Portal Users', value: summary?.total_members ?? 0, icon: Users },
    { label: 'Tenant Admins', value: summary?.tenant_admins ?? 0, icon: Building2 },
    { label: 'Users', value: summary?.users ?? 0, icon: Users },
    { label: 'Enabled Features', value: summary?.enabled_features ?? 0, icon: Sparkles },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Badge tone="info">Tenant admin workspace</Badge>
            <h1 className="mt-2 text-3xl font-semibold text-white">{currentTenant?.name ?? 'Tenant'} dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Scoped to tenant {user?.tenantId || currentTenant?.id || 'unknown'}. This workspace only shows your own tenant data.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadDashboard()} disabled={refreshing}>
            {refreshing ? 'Refreshing...' : 'Refresh'}
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
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-white">{loading ? '...' : <CountUp value={card.value} />}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Enabled Features</h2>
          <div className="grid gap-3">
            {features.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                No enabled features found for this tenant.
              </div>
            ) : (
              features.map((feature) => (
                <div key={feature.feature_code} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                  <div className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">{feature.feature_code.toUpperCase()}</div>
                  {feature.description ? <div className="mt-2 text-sm text-slate-500 dark:text-slate-400">{feature.description}</div> : null}
                </div>
              ))
            )}
          </div>
        </Card>

        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tenant Guardrails</h2>
          <div className="grid gap-3 text-sm text-slate-600 dark:text-slate-300">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              You only see portal users and features from your own tenant.
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Tenant admins can manage portal users, but cannot create tenants.
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              Role changes stay limited to tenant_admin and user.
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

import { Building2, ChevronRight, ClipboardList, RefreshCw, ShieldCheck, Sparkles, Users } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

import { ChartCard } from '@/components/dashboard/ChartCard';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { adminApi, type AdminFeatureDefinition, type AdminDashboardSummary } from '@/services/admin';
import { useApp } from '@/context/AppContext';

const COLORS = ['#22d3ee', '#60a5fa', '#f59e0b'];

function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title;
  }, [title]);
}

function CountUp({ value }: { value: number }) {
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    let frame = 0;
    const duration = 700;
    const start = performance.now();

    const animate = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      const next = Math.round(value * progress);
      setDisplayValue(next);
      if (progress < 1) {
        frame = window.requestAnimationFrame(animate);
      }
    };

    frame = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frame);
  }, [value]);

  return <span>{displayValue.toLocaleString()}</span>;
}

function formatDate(iso: string) {
  const date = new Date(iso);
  return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function metricIcon(key: string) {
  switch (key) {
    case 'total_tenants':
      return Building2;
    case 'active_tenants':
      return ShieldCheck;
    case 'tenant_admins':
      return Users;
    case 'users':
      return ClipboardList;
    case 'features':
      return Sparkles;
    case 'sessions':
      return ShieldCheck;
    default:
      return Building2;
  }
}

export function AdminDashboard() {
  const { tenants } = useApp();
  const [features, setFeatures] = useState<AdminFeatureDefinition[]>([]);
  const [summary, setSummary] = useState<AdminDashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  usePageTitle('Vision Pass | Dashboard');

  async function loadDashboard() {
    try {
      setRefreshing(true);
      const [summaryResponse, featureResponse] = await Promise.all([adminApi.getDashboardSummary(), adminApi.listFeatures()]);
      setSummary(summaryResponse);
      setFeatures(featureResponse.features);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadDashboard();
  }, []);

  const activeTenants = tenants.filter((tenant) => tenant.status === 'active');
  const recentTenants = useMemo(() => [...tenants].sort((a, b) => new Date(b.created_at ?? '').getTime() - new Date(a.created_at ?? '').getTime()).slice(0, 5), [tenants]);
  const recentFeatures = useMemo(() => [...features].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()).slice(0, 5), [features]);
  const tenantDistribution = [
    { name: 'Active', value: activeTenants.length },
    { name: 'Inactive', value: tenants.filter((tenant) => tenant.status === 'inactive').length },
    { name: 'Suspended', value: tenants.filter((tenant) => tenant.status === 'suspended').length },
  ];

  const growthData = useMemo(() => {
    const buckets = new Map<string, { label: string; tenants: number; users: number }>();
    tenants
      .filter((tenant) => tenant.created_at)
      .sort((a, b) => new Date(a.created_at ?? '').getTime() - new Date(b.created_at ?? '').getTime())
      .forEach((tenant) => {
        const date = new Date(tenant.created_at ?? '');
        const key = date.getFullYear() + '-' + date.getMonth();
        if (!buckets.has(key)) {
          buckets.set(key, { label: date.toLocaleDateString(undefined, { month: 'short' }), tenants: 0, users: 0 });
        }
        const bucket = buckets.get(key)!;
        bucket.tenants += 1;
        bucket.users += tenant.users;
      });
    const values = Array.from(buckets.values());
    return values.length > 0
      ? values.slice(-6)
      : [
          { label: 'Jan', tenants: 0, users: 0 },
          { label: 'Feb', tenants: 0, users: 0 },
          { label: 'Mar', tenants: 0, users: 0 },
        ];
  }, [tenants]);

  const metrics = [
    { key: 'total_tenants', label: 'Total Tenants', value: summary?.total_tenants ?? tenants.length, tone: 'info' as const },
    { key: 'active_tenants', label: 'Active Tenants', value: summary?.active_tenants ?? activeTenants.length, tone: 'success' as const },
    { key: 'tenant_admins', label: 'Total Tenant Admins', value: summary?.total_tenant_admins ?? 0, tone: 'warning' as const },
    { key: 'users', label: 'Total Users', value: summary?.total_users ?? tenants.reduce((sum, tenant) => sum + tenant.users, 0), tone: 'info' as const },
    { key: 'features', label: 'Total Features', value: summary?.total_features ?? features.length, tone: 'success' as const },
    { key: 'sessions', label: 'Active Sessions', value: summary?.active_sessions ?? 0, tone: 'warning' as const },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Super admin</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Super Admin Dashboard</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Monitor tenants, features, users, and audit-ready platform activity from a single command center.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadDashboard()} disabled={refreshing}>
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {metrics.map((metric) => {
          const Icon = metricIcon(metric.key);
          return (
            <Card key={metric.key} className="border-white/10 bg-gradient-to-br from-slate-950/90 to-slate-900/70 transition duration-200 hover:-translate-y-1 hover:border-cyan-400/30">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-400">{metric.label}</p>
                  <p className="mt-3 text-3xl font-semibold tracking-tight text-white">
                    {loading ? '...' : <CountUp value={metric.value} />}
                  </p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-cyan-300">
                  <Icon className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between gap-3">
                <Badge tone={metric.tone}>{metric.label}</Badge>
                <ChevronRight className="h-4 w-4 text-slate-500" />
              </div>
            </Card>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <ChartCard title="Tenant Growth" description="Tenant and user growth over recent months.">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="label" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Line type="monotone" dataKey="tenants" stroke="#22d3ee" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="users" stroke="#60a5fa" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>

        <ChartCard title="Tenant Distribution" description="Active, inactive, and suspended tenants.">
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Tooltip />
              <Pie data={tenantDistribution} dataKey="value" nameKey="name" innerRadius={72} outerRadius={112} paddingAngle={4}>
                {tenantDistribution.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 flex flex-wrap gap-2">
            {tenantDistribution.map((item, index) => (
              <Badge key={item.name} tone={index === 0 ? 'success' : index === 1 ? 'warning' : 'danger'}>
                {item.name}: {item.value}
              </Badge>
            ))}
          </div>
        </ChartCard>
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent Tenants</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Newest tenant records.</p>
            </div>
            <Link to="/admin/tenants" className="text-sm font-medium text-cyan-300 hover:text-cyan-200">
              View all
            </Link>
          </div>
          <div className="grid gap-3">
            {recentTenants.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                No tenants yet.
              </div>
            ) : (
              recentTenants.map((tenant) => (
                <div key={tenant.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{tenant.name}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{tenant.adminName ?? 'Unknown admin'}</div>
                    </div>
                    <Badge tone={tenant.status === 'active' ? 'success' : tenant.status === 'suspended' ? 'danger' : 'warning'}>{tenant.status}</Badge>
                  </div>
                  <div className="mt-3 text-sm text-slate-500 dark:text-slate-400">Created {formatDate(tenant.created_at ?? new Date().toISOString())}</div>
                </div>
              ))
            )}
          </div>
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recently Added Features</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Master feature catalog changes.</p>
            </div>
            <Link to="/admin/features" className="text-sm font-medium text-cyan-300 hover:text-cyan-200">
              Manage features
            </Link>
          </div>
          <div className="grid gap-3">
            {recentFeatures.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                No features yet.
              </div>
            ) : (
              recentFeatures.map((feature) => (
                <div key={feature.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                      <div className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">{feature.feature_code.toUpperCase()}</div>
                    </div>
                    <Badge tone={feature.status === 'active' ? 'success' : 'neutral'}>{feature.status}</Badge>
                  </div>
                  <div className="mt-3 text-sm text-slate-500 dark:text-slate-400">Created {formatDate(feature.created_at)}</div>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <ChartCard title="Tenant Count" description="Current tenant volume.">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={growthData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148, 163, 184, 0.18)" />
              <XAxis dataKey="label" stroke="#94a3b8" />
              <YAxis stroke="#94a3b8" />
              <Tooltip />
              <Bar dataKey="tenants" radius={[12, 12, 0, 0]} fill="#22d3ee" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>

        <div className="grid gap-4">
          <Card className="grid gap-3">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Quick Actions</h3>
            <div className="grid gap-3">
              <Link to="/admin/tenants" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-medium text-slate-700 transition hover:border-cyan-400/30 hover:bg-cyan-500/5 dark:border-white/10 dark:bg-white/5 dark:text-slate-100">
                Add Tenant
              </Link>
              <Link to="/admin/features" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-medium text-slate-700 transition hover:border-cyan-400/30 hover:bg-cyan-500/5 dark:border-white/10 dark:bg-white/5 dark:text-slate-100">
                Add Feature
              </Link>
              <Link to="/admin/audit-logs" className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 font-medium text-slate-700 transition hover:border-cyan-400/30 hover:bg-cyan-500/5 dark:border-white/10 dark:bg-white/5 dark:text-slate-100">
                Open Audit Logs
              </Link>
            </div>
          </Card>

          <Card className="grid gap-3">
            <h3 className="text-base font-semibold text-slate-900 dark:text-white">Platform health</h3>
            <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              <div>
                <div className="text-sm text-slate-500 dark:text-slate-400">Active sessions</div>
                <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{summary?.active_sessions ?? 0}</div>
              </div>
              <Badge tone="info">Live</Badge>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
}

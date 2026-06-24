import { useEffect, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { adminApi, type AdminTenantDetails } from '@/services/admin';
import { usePageTitle } from '@/hooks/usePageTitle';

function formatDate(value?: string) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(value?: string) {
  if (!value) return '-';
  return new Date(value).toLocaleString(undefined, { month: 'short', day: 'numeric', year: 'numeric', hour: 'numeric', minute: '2-digit' });
}

function statusTone(status: string) {
  if (status === 'active') return 'success' as const;
  if (status === 'suspended') return 'danger' as const;
  return 'warning' as const;
}

export function TenantDetails() {
  const { tenantId } = useParams();
  const [details, setDetails] = useState<AdminTenantDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  usePageTitle(details ? 'VisionPass AI | ' + details.tenant.name : 'VisionPass AI | Tenant Details');

  useEffect(() => {
    let active = true;

    async function loadTenant() {
      if (!tenantId) return;
      try {
        setLoading(true);
        const data = await adminApi.getTenantDetails(tenantId);
        if (!active) return;
        setDetails(data);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Unable to load tenant.');
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadTenant();
    return () => {
      active = false;
    };
  }, [tenantId]);

  if (!tenantId) return <Navigate to="/admin/tenants" replace />;
  if (!loading && !details && !error) return <Navigate to="/admin/tenants" replace />;

  const tenant = details?.tenant ?? null;

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Badge tone="info">Tenant details</Badge>
            <h1 className="mt-2 text-3xl font-semibold text-white">{tenant?.name ?? 'Tenant'}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Review organization information, assigned features, tenant admins, users, and activity summary.
            </p>
          </div>
          <div className="flex gap-2">
            <Link to="/admin/tenants">
              <Button variant="secondary">Back to tenants</Button>
            </Link>
            {tenant ? (
              <Link to={'/admin/tenants'}>
                <Button>Manage tenant</Button>
              </Link>
            ) : null}
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: 'Tenant Admins', value: details?.activitySummary.tenant_admins ?? 0 },
          { label: 'Total Users', value: details?.activitySummary.total_users ?? 0 },
          { label: 'Assigned Features', value: details?.activitySummary.assigned_features ?? 0 },
          { label: 'Active Users', value: details?.activitySummary.active_users ?? 0 },
        ].map((item) => (
          <Card key={item.label} className="grid gap-2">
            <div className="text-sm text-slate-500 dark:text-slate-400">{item.label}</div>
            <div className="text-3xl font-semibold text-slate-900 dark:text-white">{loading ? '...' : item.value}</div>
          </Card>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Organization Information</h2>
          {tenant ? (
            <div className="grid gap-3">
              {[
                { label: 'Company Name', value: tenant.name },
                { label: 'Company Email', value: tenant.adminEmail ?? '-' },
                { label: 'Phone', value: tenant.phone ?? '-' },
                { label: 'Address', value: tenant.address ?? '-' },
                { label: 'Logo URL', value: tenant.logo_url ?? '-' },
                { label: 'Status', value: tenant.status },
                { label: 'Created Date', value: formatDate(tenant.created_at) },
              ].map((item) => (
                <div key={item.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{item.label}</div>
                  <div className="mt-2 font-medium text-slate-900 dark:text-white">{item.label === 'Status' ? <Badge tone={statusTone(item.value)}>{item.value}</Badge> : item.value}</div>
                </div>
              ))}
            </div>
          ) : null}
        </Card>

        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Assigned Features</h2>
          <div className="grid gap-3">
            {details?.assignedFeatures.length ? (
              details.assignedFeatures.map((feature) => (
                <div key={feature.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                      <div className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">{feature.feature_code.toUpperCase()}</div>
                    </div>
                    <Badge tone={feature.status === 'active' ? 'success' : 'neutral'}>{feature.status}</Badge>
                  </div>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
                No features assigned yet.
              </div>
            )}
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tenant Admins</h2>
          {details?.admins.length ? (
            <div className="grid gap-3">
              {details.admins.map((admin) => (
                <div key={admin.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{admin.name}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{admin.email}</div>
                    </div>
                    <Badge tone={admin.isActive ? 'success' : 'warning'}>{admin.role}</Badge>
                  </div>
                  <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">Joined {formatDateTime(admin.createdAt)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
              No tenant admins found.
            </div>
          )}
        </Card>

        <Card className="grid gap-4">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Users</h2>
          {details?.users.length ? (
            <div className="grid gap-3">
              {details.users.map((user) => (
                <div key={user.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{user.name}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{user.email}</div>
                    </div>
                    <Badge tone={user.isActive ? 'success' : 'warning'}>{user.role}</Badge>
                  </div>
                  <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">Joined {formatDateTime(user.createdAt)}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
              No users found.
            </div>
          )}
        </Card>
      </div>

      <Card className="grid gap-4">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Activity Summary</h2>
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
          {Object.entries(details?.activitySummary ?? {}).map(([key, value]) => (
            <div key={key} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{key.replace(/_/g, ' ')}</div>
              <div className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{value}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

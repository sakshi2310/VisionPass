import { Eye, Pencil, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { adminApi, type AdminFeatureDefinition, type AdminTenant } from '@/services/admin';

function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title;
  }, [title]);
}

type TenantDraft = {
  organization_name: string;
  full_name: string;
  company_email: string;
  admin_email: string;
  phone: string;
  password: string;
  address: string;
  logo_url: string;
  status: 'active' | 'inactive' | 'suspended';
  industry: string;
  max_users: number;
  max_devices: number;
  enabled_modules: string[];
};

type Mode = 'create' | 'edit' | null;

const emptyDraft: TenantDraft = {
  organization_name: '',
  full_name: '',
  company_email: '',
  admin_email: '',
  phone: '',
  password: '',
  address: '',
  logo_url: '',
  status: 'active',
  industry: 'General',
  max_users: 100,
  max_devices: 20,
  enabled_modules: [],
};

function tenantStatusTone(status: AdminTenant['status']) {
  if (status === 'active') return 'success' as const;
  if (status === 'suspended') return 'danger' as const;
  return 'warning' as const;
}

function formatDate(value?: string) {
  if (!value) return '-';
  return new Date(value).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

export function Tenants() {
  const [tenants, setTenants] = useState<AdminTenant[]>([]);
  const [features, setFeatures] = useState<AdminFeatureDefinition[]>([]);
  const [mode, setMode] = useState<Mode>(null);
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);
  const [draft, setDraft] = useState<TenantDraft>(emptyDraft);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive' | 'suspended'>('all');
  const [page, setPage] = useState(1);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const pageSize = 10;

  usePageTitle('Vision Pass | Tenants');

  const activeFeatures = useMemo(() => features.filter((feature) => feature.status === 'active'), [features]);

  const filteredTenants = useMemo(() => {
    const term = search.trim().toLowerCase();
    return tenants.filter((tenant) => {
      const matchesSearch =
        !term ||
        [tenant.name, tenant.companyEmail ?? '', tenant.adminName ?? '', tenant.adminEmail ?? '', tenant.phone ?? ''].some((value) =>
          value.toLowerCase().includes(term),
        );
      const matchesStatus = statusFilter === 'all' || tenant.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [search, statusFilter, tenants]);

  const totalPages = Math.max(1, Math.ceil(filteredTenants.length / pageSize));
  const visibleTenants = useMemo(() => filteredTenants.slice((page - 1) * pageSize, page * pageSize), [filteredTenants, page]);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  async function loadTenants() {
    try {
      setError('');
      setRefreshing(true);
      const [tenantResponse, featureResponse] = await Promise.all([adminApi.listTenants(), adminApi.listFeatures()]);
      setTenants(tenantResponse);
      setFeatures(featureResponse.features);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tenants.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadTenants();
  }, []);

  function openCreate() {
    setMode('create');
    setSelectedTenantId(null);
    setDraft(emptyDraft);
    setError('');
  }

  function openEdit(tenant: AdminTenant) {
    setMode('edit');
    setSelectedTenantId(tenant.id);
    setDraft({
      organization_name: tenant.name,
      full_name: tenant.adminName ?? '',
      company_email: tenant.companyEmail ?? '',
      admin_email: tenant.adminEmail ?? '',
      phone: tenant.phone ?? '',
      password: '',
      address: tenant.address ?? '',
      logo_url: tenant.logo_url ?? '',
      status: tenant.status as TenantDraft['status'],
      industry: tenant.industry,
      max_users: tenant.maxUsers ?? 100,
      max_devices: tenant.maxDevices ?? 20,
      enabled_modules: tenant.enabledModules,
    });
    setError('');
  }

  function closeModal() {
    setMode(null);
    setSelectedTenantId(null);
    setDraft(emptyDraft);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.organization_name.trim() || !draft.company_email.trim() || !draft.full_name.trim() || !draft.admin_email.trim()) {
      setError('Company name, company email, admin name, and admin email are required.');
      return;
    }
    if (mode === 'create' && !draft.password.trim()) {
      setError('Password is required when creating a tenant.');
      return;
    }
    setSaving(true);
    setError('');
    try {
      if (mode === 'create') {
        await adminApi.createTenant({
          full_name: draft.full_name,
          email: draft.admin_email,
          company_email: draft.company_email,
          phone: draft.phone || undefined,
          password: draft.password,
          organization_name: draft.organization_name,
          logo_url: draft.logo_url || undefined,
          address: draft.address || undefined,
          status: draft.status,
          industry: draft.industry,
          max_users: draft.max_users,
          max_devices: draft.max_devices,
          enabled_modules: draft.enabled_modules,
        });
      } else if (selectedTenantId) {
        await adminApi.updateTenant(selectedTenantId, {
          name: draft.organization_name,
          company_email: draft.company_email,
          admin_name: draft.full_name,
          admin_email: draft.admin_email,
          phone: draft.phone,
          logo_url: draft.logo_url,
          address: draft.address,
          status: draft.status,
          industry: draft.industry,
          max_users: draft.max_users,
          max_devices: draft.max_devices,
          enabled_modules: draft.enabled_modules,
        });
      }
      await loadTenants();
      closeModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save tenant.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(tenantId: string) {
    try {
      await adminApi.deleteTenant(tenantId);
      await loadTenants();
      if (selectedTenantId === tenantId) closeModal();
      setPendingDeleteId(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete tenant.');
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Tenant management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Tenants</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Search tenants, filter by status, refresh the table, or create a new tenant with its first admin.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadTenants()} disabled={refreshing}>
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Create Tenant
            </Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-slate-950/75 lg:grid-cols-[1fr_auto] lg:items-end">
        <Input label="Search tenant" placeholder="Company, email, phone" value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="h-4 w-4" />} />
        <label className="grid gap-2">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="h-11 min-w-[220px] rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white">
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>
        </label>
      </section>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tenant list</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">{filteredTenants.length} tenants match the current filters.</p>
            </div>
            <Badge tone="neutral">Page {page} of {totalPages}</Badge>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-white/10">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-950/40 dark:text-slate-400">
              <tr>
                <th className="px-5 py-4 font-medium">Company Name</th>
                <th className="px-5 py-4 font-medium">Company Email</th>
                <th className="px-5 py-4 font-medium">Phone</th>
                <th className="px-5 py-4 font-medium">Status</th>
                <th className="px-5 py-4 font-medium">Created Date</th>
                <th className="px-5 py-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white dark:divide-white/10 dark:bg-slate-950/40">
              {loading ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={6}>Loading tenants...</td>
                </tr>
              ) : visibleTenants.length === 0 ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={6}>No tenants found.</td>
                </tr>
              ) : (
                visibleTenants.map((tenant) => (
                  <tr key={tenant.id}>
                    <td className="px-5 py-4 align-top">
                      <div className="font-medium text-slate-900 dark:text-white">{tenant.name}</div>
                      <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{tenant.industry}</div>
                    </td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{tenant.companyEmail ?? '-'}</td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{tenant.phone ?? '-'}</td>
                    <td className="px-5 py-4 align-top"><Badge tone={tenantStatusTone(tenant.status)}>{tenant.status}</Badge></td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{formatDate(tenant.created_at)}</td>
                    <td className="px-5 py-4 align-top">
                      <div className="flex flex-wrap gap-2">
                        <Link to={'/admin/tenants/' + tenant.id} className="inline-flex">
                          <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />}>View</Button>
                        </Link>
                        <Button variant="secondary" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(tenant)}>Edit</Button>
                        <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setPendingDeleteId(tenant.id)}>Delete</Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filteredTenants.length)} of {filteredTenants.length} tenants
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>Previous</Button>
            <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>Next</Button>
          </div>
        </div>
      </Card>

      <Modal
        open={mode !== null}
        title={mode === 'create' ? 'Create tenant' : 'Edit tenant'}
        description={mode === 'create' ? 'Create an organization, its first tenant admin, and assigned features.' : 'Edit tenant details in the pop-up form.'}
        onClose={closeModal}
        className="max-w-5xl"
        footer={
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-slate-500 dark:text-slate-400">The form saves the tenant record, first admin, and feature assignments together.</div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={closeModal}>Cancel</Button>
              <Button type="submit" form="tenant-form" leftIcon={<Pencil className="h-4 w-4" />} disabled={saving}>
                {saving ? 'Saving...' : mode === 'create' ? 'Create tenant' : 'Save tenant'}
              </Button>
            </div>
          </div>
        }
      >
        <form id="tenant-form" onSubmit={handleSubmit} className="grid gap-6">
          <div className="grid gap-4 xl:grid-cols-2">
            <Card className="grid gap-4 p-4 shadow-none">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">Organization Details</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <Input label="Company Name" value={draft.organization_name} onChange={(event) => setDraft((current) => ({ ...current, organization_name: event.target.value }))} />
                <Input label="Company Email" type="email" value={draft.company_email} onChange={(event) => setDraft((current) => ({ ...current, company_email: event.target.value }))} />
                <Input label="Phone" value={draft.phone} onChange={(event) => setDraft((current) => ({ ...current, phone: event.target.value }))} />
                <Input label="Address" value={draft.address} onChange={(event) => setDraft((current) => ({ ...current, address: event.target.value }))} />
                <Input label="Logo URL" value={draft.logo_url} onChange={(event) => setDraft((current) => ({ ...current, logo_url: event.target.value }))} helpText="Optional logo location or uploaded asset URL." />
                <label className="grid gap-2">
                  <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Status</span>
                  <select value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as TenantDraft['status'] }))} className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white">
                    <option value="active">active</option>
                    <option value="inactive">inactive</option>
                    <option value="suspended">suspended</option>
                  </select>
                </label>
              </div>
            </Card>

            <Card className="grid gap-4 p-4 shadow-none">
              <h3 className="text-base font-semibold text-slate-900 dark:text-white">First Tenant Admin</h3>
              <div className="grid gap-4 md:grid-cols-2">
                <Input label="Admin Name" value={draft.full_name} onChange={(event) => setDraft((current) => ({ ...current, full_name: event.target.value }))} />
                <Input label="Admin Email" type="email" value={draft.admin_email} onChange={(event) => setDraft((current) => ({ ...current, admin_email: event.target.value }))} />
                {mode === 'create' ? (
                  <Input label="Admin Password" type="password" value={draft.password} onChange={(event) => setDraft((current) => ({ ...current, password: event.target.value }))} />
                ) : (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400 md:col-span-2">
                    Password changes stay in the account flow.
                  </div>
                )}
                <Input label="Industry" value={draft.industry} onChange={(event) => setDraft((current) => ({ ...current, industry: event.target.value }))} />
                <Input label="Max Users" type="number" min="1" value={draft.max_users} onChange={(event) => setDraft((current) => ({ ...current, max_users: Number(event.target.value) }))} />
                <Input label="Max Devices" type="number" min="1" value={draft.max_devices} onChange={(event) => setDraft((current) => ({ ...current, max_devices: Number(event.target.value) }))} />
              </div>
            </Card>
          </div>

          <Card className="grid gap-4 p-4 shadow-none">
            <div className="flex items-center justify-between gap-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">Enabled Features</h3>
                <p className="text-sm text-slate-500 dark:text-slate-400">Select the features this tenant can use.</p>
              </div>
              <Badge tone="neutral">{draft.enabled_modules.length} selected</Badge>
            </div>
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {activeFeatures.map((feature) => {
                const enabled = draft.enabled_modules.includes(feature.feature_code);
                return (
                  <button
                    key={feature.id}
                    type="button"
                    onClick={() =>
                      setDraft((current) => ({
                        ...current,
                        enabled_modules: enabled
                          ? current.enabled_modules.filter((item) => item !== feature.feature_code)
                          : current.enabled_modules.concat(feature.feature_code),
                      }))
                    }
                    className={enabled ? 'rounded-2xl border border-cyan-400/40 bg-cyan-500/10 px-4 py-3 text-left' : 'rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 text-left hover:border-slate-300 dark:border-white/10 dark:bg-white/5'}
                  >
                    <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                    <div className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">{feature.feature_code.toUpperCase()}</div>
                  </button>
                );
              })}
            </div>
          </Card>
        </form>
      </Modal>

      <Modal
        open={pendingDeleteId !== null}
        title="Delete tenant"
        description="This will soft-delete the tenant and mark access inactive."
        onClose={() => setPendingDeleteId(null)}
        className="max-w-xl"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setPendingDeleteId(null)}>Cancel</Button>
            <Button variant="danger" onClick={() => pendingDeleteId && void handleDelete(pendingDeleteId)}>Delete tenant</Button>
          </div>
        }
      >
        <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
          Deleting a tenant hides it from active administration views while keeping historical records intact.
        </p>
      </Modal>
    </div>
  );
}

import { Eye, Pencil, Plus, RefreshCw, Search, Trash2 } from 'lucide-react';
import { FormEvent, useEffect, useMemo, useState } from 'react';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import { adminApi, type AdminFeatureDefinition } from '@/services/admin';

function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title;
  }, [title]);
}

function buildFeatureCode(name: string) {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '');
}

type FeatureDraft = {
  feature_name: string;
  feature_code: string;
  description: string;
  status: 'active' | 'inactive';
};

type Mode = 'create' | 'edit' | null;

const emptyDraft: FeatureDraft = {
  feature_name: '',
  feature_code: '',
  description: '',
  status: 'active',
};

export function Features() {
  const [features, setFeatures] = useState<AdminFeatureDefinition[]>([]);
  const [draft, setDraft] = useState<FeatureDraft>(emptyDraft);
  const [mode, setMode] = useState<Mode>(null);
  const [selectedFeatureId, setSelectedFeatureId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'active' | 'inactive'>('all');
  const [page, setPage] = useState(1);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const pageSize = 10;

  usePageTitle('Vision Pass | Features');

  const selectedFeature = useMemo(() => features.find((feature) => feature.id === selectedFeatureId) ?? null, [features, selectedFeatureId]);

  const filteredFeatures = useMemo(() => {
    const term = search.trim().toLowerCase();
    return features.filter((feature) => {
      const matchesSearch =
        !term ||
        [feature.feature_name, feature.feature_code, feature.description ?? ''].some((value) => value.toLowerCase().includes(term));
      const matchesStatus = statusFilter === 'all' || feature.status === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [features, search, statusFilter]);

  const totalPages = Math.max(1, Math.ceil(filteredFeatures.length / pageSize));
  const visibleFeatures = useMemo(() => filteredFeatures.slice((page - 1) * pageSize, page * pageSize), [filteredFeatures, page]);

  useEffect(() => {
    setPage(1);
  }, [search, statusFilter]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  async function loadFeatures() {
    try {
      setError('');
      setRefreshing(true);
      const response = await adminApi.listFeatures();
      setFeatures(response.features);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load features.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadFeatures();
  }, []);

  function openCreate() {
    setMode('create');
    setDraft(emptyDraft);
    setSelectedFeatureId(null);
    setError('');
  }

  function openEdit(feature: AdminFeatureDefinition) {
    setMode('edit');
    setSelectedFeatureId(feature.id);
    setDraft({
      feature_name: feature.feature_name,
      feature_code: feature.feature_code,
      description: feature.description ?? '',
      status: feature.status === 'inactive' ? 'inactive' : 'active',
    });
    setError('');
  }

  function closeModal() {
    setMode(null);
    setSelectedFeatureId(null);
    setDraft(emptyDraft);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.feature_name.trim()) {
      setError('Feature name is required.');
      return;
    }
    const featureCode = draft.feature_code.trim() || buildFeatureCode(draft.feature_name);
    setSaving(true);
    setError('');
    try {
      if (mode === 'create') {
        await adminApi.createFeature({
          feature_name: draft.feature_name,
          feature_code: featureCode,
          description: draft.description,
          status: draft.status,
        });
      } else if (selectedFeatureId) {
        await adminApi.updateFeature(selectedFeatureId, {
          feature_name: draft.feature_name,
          feature_code: featureCode,
          description: draft.description,
          status: draft.status,
        });
      }
      await loadFeatures();
      closeModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save feature.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!pendingDeleteId) return;
    try {
      await adminApi.deleteFeature(pendingDeleteId);
      await loadFeatures();
      setPendingDeleteId(null);
      if (selectedFeatureId === pendingDeleteId) {
        closeModal();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to delete feature.');
    }
  }

  async function toggleStatus(feature: AdminFeatureDefinition) {
    await adminApi.updateFeature(feature.id, {
      status: feature.status === 'active' ? 'inactive' : 'active',
    });
    await loadFeatures();
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Master features</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Feature management</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Create, update, enable, disable, or remove master features that can be assigned to tenants.
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadFeatures()} disabled={refreshing}>
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Create Feature
            </Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-slate-950/75 lg:grid-cols-[1.3fr_auto] lg:items-end">
        <Input label="Search features" value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search by name or code" leftIcon={<Search className="h-4 w-4" />} />
        <label className="grid gap-2">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Status</span>
          <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)} className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white">
            <option value="all">All statuses</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </label>
      </section>

      <Card className="overflow-hidden p-0">
        <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Feature table</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">{filteredFeatures.length} features in the catalog.</p>
            </div>
            <Badge tone="neutral">Page {page} of {totalPages}</Badge>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 dark:divide-white/10">
            <thead className="bg-slate-50 text-left text-xs uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-950/40 dark:text-slate-400">
              <tr>
                <th className="px-5 py-4 font-medium">Feature Name</th>
                <th className="px-5 py-4 font-medium">Active Status</th>
                <th className="px-5 py-4 font-medium">Created Date</th>
                <th className="px-5 py-4 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 bg-white dark:divide-white/10 dark:bg-slate-950/40">
              {loading ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={4}>Loading features...</td>
                </tr>
              ) : visibleFeatures.length === 0 ? (
                <tr>
                  <td className="px-5 py-8 text-sm text-slate-500 dark:text-slate-400" colSpan={4}>No features found.</td>
                </tr>
              ) : (
                visibleFeatures.map((feature) => (
                  <tr key={feature.id}>
                    <td className="px-5 py-4 align-top">
                      <div className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</div>
                      <div className="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">{feature.feature_code.toUpperCase()}</div>
                    </td>
                    <td className="px-5 py-4 align-top">
                      <Badge tone={feature.status === 'active' ? 'success' : 'neutral'}>{feature.status}</Badge>
                    </td>
                    <td className="px-5 py-4 align-top text-sm text-slate-600 dark:text-slate-300">{new Date(feature.created_at).toLocaleDateString()}</td>
                    <td className="px-5 py-4 align-top">
                      <div className="flex flex-wrap gap-2">
                        <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => openEdit(feature)}>View / Edit</Button>
                        <Button variant="secondary" size="sm" onClick={() => void toggleStatus(feature)}>
                          {feature.status === 'active' ? 'Disable' : 'Enable'}
                        </Button>
                        <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setPendingDeleteId(feature.id)}>Delete</Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between gap-3 border-t border-slate-200 px-5 py-4 dark:border-white/10">
          <div className="text-sm text-slate-500 dark:text-slate-400">
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filteredFeatures.length)} of {filteredFeatures.length} features
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>Previous</Button>
            <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>Next</Button>
          </div>
        </div>
      </Card>

      <Modal
        open={mode !== null}
        title={mode === 'create' ? 'Create feature' : 'Edit feature'}
        description={mode === 'create' ? 'Add a new master feature.' : 'Update the master feature metadata.'}
        onClose={closeModal}
        className="max-w-3xl"
        footer={
          <div className="flex items-center justify-between gap-3">
            <div className="text-sm text-slate-500 dark:text-slate-400">Use the form to keep the master catalog in sync with product capabilities.</div>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={closeModal}>Cancel</Button>
              <Button type="submit" form="feature-form" leftIcon={<Pencil className="h-4 w-4" />} disabled={saving}>
                {saving ? 'Saving...' : mode === 'create' ? 'Create feature' : 'Save feature'}
              </Button>
            </div>
          </div>
        }
      >
        <form id="feature-form" onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Feature name" value={draft.feature_name} onChange={(event) => setDraft((current) => ({ ...current, feature_name: event.target.value, feature_code: current.feature_code || buildFeatureCode(event.target.value) }))} placeholder="Object Detection" />
            <Input label="Feature code" value={draft.feature_code} onChange={(event) => setDraft((current) => ({ ...current, feature_code: event.target.value }))} placeholder="object_detection" helpText="Auto-generated from the name if left blank." />
          </div>
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Description</span>
            <textarea
              rows={4}
              value={draft.description}
              onChange={(event) => setDraft((current) => ({ ...current, description: event.target.value }))}
              className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-slate-900 outline-none focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-white"
              placeholder="Describe what the feature does"
            />
          </label>
          <label className="grid gap-2 md:max-w-xs">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Active status</span>
            <select value={draft.status} onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as FeatureDraft['status'] }))} className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white">
              <option value="active">active</option>
              <option value="inactive">inactive</option>
            </select>
          </label>
        </form>
      </Modal>

      <Modal
        open={pendingDeleteId !== null}
        title="Permanently delete feature"
        description="This removes the feature and all tenant/member assignments. Use Disable if you may enable it again later."
        onClose={() => setPendingDeleteId(null)}
        className="max-w-xl"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setPendingDeleteId(null)}>Cancel</Button>
            <Button variant="danger" onClick={() => void handleDelete()}>Delete feature</Button>
          </div>
        }
      >
        <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
          This action cannot be undone. Disabled features remain in this table with inactive status; deleted features do not.
        </p>
      </Modal>
    </div>
  );
}

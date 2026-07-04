import { useEffect, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';

import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import { Toast } from '@/components/ui/Toast';
import { adminApi, type AdminFaceSettings, type AdminTenantDetails } from '@/services/admin';
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

type ToastState = {
  tone: 'success' | 'error';
  title: string;
  message: string;
} | null;

function faceSettingsToDraft(settings: AdminFaceSettings) {
  return {
    face_match_threshold: String(settings.face_match_threshold),
    min_face_images: String(settings.min_face_images),
    recommended_face_images: String(settings.recommended_face_images),
    max_face_images: String(settings.max_face_images),
    min_face_size_px: String(settings.min_face_size_px),
    min_resolution_width: String(settings.min_resolution_width),
    min_resolution_height: String(settings.min_resolution_height),
    max_blur_score: String(settings.max_blur_score),
    min_brightness: String(settings.min_brightness),
    max_brightness: String(settings.max_brightness),
    embedding_model: settings.embedding_model,
    embedding_version: settings.embedding_version ?? '',
    embedding_dimension: String(settings.embedding_dimension),
    is_active: settings.is_active,
  };
}

export function TenantDetails() {
  const { tenantId } = useParams();
  const [details, setDetails] = useState<AdminTenantDetails | null>(null);
  const [faceSettings, setFaceSettings] = useState<AdminFaceSettings | null>(null);
  const [faceDraft, setFaceDraft] = useState(faceSettingsToDraft({
    id: '', tenant_id: '', face_match_threshold: 0.65, min_face_images: 3, recommended_face_images: 5, max_face_images: 10,
    min_face_size_px: 64, min_resolution_width: 320, min_resolution_height: 240, max_blur_score: 120, min_brightness: 35,
    max_brightness: 220, embedding_model: 'buffalo_l', embedding_version: 'v1', embedding_dimension: 512,
    is_active: true, created_at: '', updated_at: '',
  }));
  const [loading, setLoading] = useState(true);
  const [savingFace, setSavingFace] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle(details ? 'Vision Pass | ' + details.tenant.name : 'Vision Pass | Tenant Details');

  useEffect(() => {
    let active = true;

    async function loadTenant() {
      if (!tenantId) return;
      try {
        setLoading(true);
        const [data, face] = await Promise.all([adminApi.getTenantDetails(tenantId), adminApi.getTenantFaceSettings(tenantId)]);
        if (!active) return;
        setDetails(data);
        setFaceSettings(face);
        setFaceDraft(faceSettingsToDraft(face));
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

  async function saveFaceSettings() {
    if (!tenantId) return;
    try {
      setSavingFace(true);
      const updated = await adminApi.updateTenantFaceSettings(tenantId, {
        face_match_threshold: Number(faceDraft.face_match_threshold),
        min_face_images: Number(faceDraft.min_face_images),
        recommended_face_images: Number(faceDraft.recommended_face_images),
        max_face_images: Number(faceDraft.max_face_images),
        min_face_size_px: Number(faceDraft.min_face_size_px),
        min_resolution_width: Number(faceDraft.min_resolution_width),
        min_resolution_height: Number(faceDraft.min_resolution_height),
        max_blur_score: Number(faceDraft.max_blur_score),
        min_brightness: Number(faceDraft.min_brightness),
        max_brightness: Number(faceDraft.max_brightness),
        embedding_model: faceDraft.embedding_model,
        embedding_version: faceDraft.embedding_version || null,
        embedding_dimension: Number(faceDraft.embedding_dimension),
        is_active: faceDraft.is_active,
      });
      setFaceSettings(updated);
      setToast({ tone: 'success', title: 'Face settings saved', message: 'The tenant-level face controls were updated.' });
    } catch (err) {
      setToast({ tone: 'error', title: 'Save failed', message: err instanceof Error ? err.message : 'Unable to save face settings.' });
    } finally {
      setSavingFace(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <Badge tone="info">Tenant details</Badge>
            <h1 className="mt-2 text-3xl font-semibold text-white">{tenant?.name ?? 'Tenant'}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Review organization information, assigned features, tenant admins, users, and the tenant face controls.
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
                { label: 'Company Email', value: tenant.companyEmail ?? '-' },
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

      <Card className="grid gap-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Tenant Face Controls</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Editable only by Super Admin. Client Admin does not see these controls.</p>
          </div>
          <Badge tone={faceSettings?.is_active ? 'success' : 'neutral'}>{faceSettings?.is_active ? 'Active' : 'Inactive'}</Badge>
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          <Input label="Match threshold" type="number" step="0.01" min={0} max={1} value={faceDraft.face_match_threshold} onChange={(event) => setFaceDraft((current) => ({ ...current, face_match_threshold: event.target.value }))} />
          <Input label="Min face images" type="number" min={1} value={faceDraft.min_face_images} onChange={(event) => setFaceDraft((current) => ({ ...current, min_face_images: event.target.value }))} />
          <Input label="Recommended images" type="number" min={1} value={faceDraft.recommended_face_images} onChange={(event) => setFaceDraft((current) => ({ ...current, recommended_face_images: event.target.value }))} />
          <Input label="Max face images" type="number" min={1} value={faceDraft.max_face_images} onChange={(event) => setFaceDraft((current) => ({ ...current, max_face_images: event.target.value }))} />
          <Input label="Min face size px" type="number" min={1} value={faceDraft.min_face_size_px} onChange={(event) => setFaceDraft((current) => ({ ...current, min_face_size_px: event.target.value }))} />
          <Input label="Min resolution width" type="number" min={1} value={faceDraft.min_resolution_width} onChange={(event) => setFaceDraft((current) => ({ ...current, min_resolution_width: event.target.value }))} />
          <Input label="Min resolution height" type="number" min={1} value={faceDraft.min_resolution_height} onChange={(event) => setFaceDraft((current) => ({ ...current, min_resolution_height: event.target.value }))} />
          <Input label="Max blur score" type="number" step="0.01" min={0} value={faceDraft.max_blur_score} onChange={(event) => setFaceDraft((current) => ({ ...current, max_blur_score: event.target.value }))} />
          <Input label="Min brightness" type="number" step="0.01" min={0} value={faceDraft.min_brightness} onChange={(event) => setFaceDraft((current) => ({ ...current, min_brightness: event.target.value }))} />
          <Input label="Max brightness" type="number" step="0.01" min={0} value={faceDraft.max_brightness} onChange={(event) => setFaceDraft((current) => ({ ...current, max_brightness: event.target.value }))} />
          <Input label="Embedding model" value={faceDraft.embedding_model} onChange={(event) => setFaceDraft((current) => ({ ...current, embedding_model: event.target.value }))} />
          <Input label="Embedding version" value={faceDraft.embedding_version} onChange={(event) => setFaceDraft((current) => ({ ...current, embedding_version: event.target.value }))} />
          <Input label="Embedding dimension" type="number" min={1} value={faceDraft.embedding_dimension} onChange={(event) => setFaceDraft((current) => ({ ...current, embedding_dimension: event.target.value }))} />
        </div>
        <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
          <input type="checkbox" checked={faceDraft.is_active} onChange={(event) => setFaceDraft((current) => ({ ...current, is_active: event.target.checked }))} />
          Face controls active
        </label>
        <div className="flex justify-end">
          <Button onClick={() => void saveFaceSettings()} disabled={savingFace || loading}> {savingFace ? 'Saving...' : 'Save face controls'} </Button>
        </div>
      </Card>

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

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        </div>
      ) : null}
    </div>
  );
}

import { PencilLine, Plus, RefreshCw, Search, Trash2, UserRoundCog } from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { formatDate } from "@/utils/format";
import { tenantAdminApi, type TenantAdminFeature, type TenantAdminMember, type TenantAdminMemberPayload } from "@/services/tenantAdmin";

type Mode = "create" | "edit";

type Draft = {
  full_name: string;
  email: string;
  password: string;
  role: "tenant_admin" | "user";
  status: "active" | "inactive" | "suspended";
};

const emptyDraft: Draft = {
  full_name: "",
  email: "",
  password: "",
  role: "user",
  status: "active",
};

function roleLabel(role: TenantAdminMember["role"]) {
  return role.toUpperCase() === "TENANT_ADMIN" ? "tenant_admin" : "user";
}

function statusTone(status: TenantAdminMember["status"]) {
  if (status === "active") return "success" as const;
  if (status === "suspended") return "warning" as const;
  return "danger" as const;
}

export function TenantAdminMembers() {
  const { currentTenant, user, refreshSession } = useApp();
  const [members, setMembers] = useState<TenantAdminMember[]>([]);
  const [featureOptions, setFeatureOptions] = useState<TenantAdminFeature[]>([]);
  const [selectedFeatureCodes, setSelectedFeatureCodes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [mode, setMode] = useState<Mode | null>(null);
  const [activeMember, setActiveMember] = useState<TenantAdminMember | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [pendingDelete, setPendingDelete] = useState<TenantAdminMember | null>(null);
  const openEditRequestId = useRef(0);
  const pageSize = 8;

  usePageTitle("Vision Pass | Portal Users");

  async function loadMembers() {
    try {
      setError("");
      setRefreshing(true);
      const response = await tenantAdminApi.listMembers();
      setMembers(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load portal users.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function loadFeatureOptions() {
    try {
      const response = await tenantAdminApi.listFeatures();
      setFeatureOptions(response);
    } catch {
      setFeatureOptions([]);
    }
  }

  useEffect(() => {
    void loadMembers();
    void loadFeatureOptions();
  }, []);

  useEffect(() => {
    setPage(1);
  }, [search]);

  const filteredMembers = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return members;
    return members.filter((member) => [member.full_name, member.email, roleLabel(member.role), member.status].some((value) => value.toLowerCase().includes(term)));
  }, [members, search]);

  const totalPages = Math.max(1, Math.ceil(filteredMembers.length / pageSize));
  const visibleMembers = useMemo(() => filteredMembers.slice((page - 1) * pageSize, page * pageSize), [filteredMembers, page]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  function openCreate() {
    openEditRequestId.current += 1;
    setMode("create");
    setActiveMember(null);
    setDraft(emptyDraft);
    setSelectedFeatureCodes([]);
    setError("");
  }

  async function openEdit(member: TenantAdminMember) {
    const requestId = ++openEditRequestId.current;
    setMode("edit");
    setActiveMember(null);
    setDraft(emptyDraft);
    setSelectedFeatureCodes([]);
    try {
      const latest = await tenantAdminApi.getMember(member.id);
      if (openEditRequestId.current !== requestId) return;
      setActiveMember(latest);
      setDraft({
        full_name: latest.full_name,
        email: latest.email,
        password: "",
        role: latest.role.toUpperCase() === "TENANT_ADMIN" ? "tenant_admin" : "user",
        status: latest.status,
      });
      setSelectedFeatureCodes(latest.assigned_features ?? []);
      setError("");
    } catch (err) {
      if (openEditRequestId.current !== requestId) return;
      setError(err instanceof Error ? err.message : "Unable to load portal user.");
      setMode(null);
      setActiveMember(null);
      setDraft(emptyDraft);
      setSelectedFeatureCodes([]);
    }
  }

  function closeModal() {
    openEditRequestId.current += 1;
    setMode(null);
    setActiveMember(null);
    setDraft(emptyDraft);
    setSelectedFeatureCodes([]);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!draft.full_name.trim()) {
      setError("Name is required.");
      return;
    }
    if (!draft.email.trim()) {
      setError("Email is required.");
      return;
    }
    if (mode === "create" && !draft.password.trim()) {
      setError("Password is required when creating a portal user.");
      return;
    }
    if (mode === "edit" && !activeMember) {
      return;
    }

    try {
      setSaving(true);
      setError("");
      const payload: TenantAdminMemberPayload = {
        full_name: draft.full_name.trim(),
        email: draft.email.trim(),
        password: draft.password.trim(),
        role: draft.role,
        status: draft.status,
        assigned_features: selectedFeatureCodes,
      };

      if (mode === "create") {
        await tenantAdminApi.createMember(payload);
      } else if (activeMember) {
        const updatePayload: Partial<TenantAdminMemberPayload> = {
          full_name: payload.full_name,
          email: payload.email,
          role: payload.role,
          status: payload.status,
          assigned_features: selectedFeatureCodes,
        };
        if (payload.password) updatePayload.password = payload.password;
        await tenantAdminApi.updateMember(activeMember.id, updatePayload);
      }
      await loadMembers();
      if (mode === "edit" && activeMember && user?.id === activeMember.id) {
        await refreshSession();
      }
      closeModal();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save portal user.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(member: TenantAdminMember) {
    const confirmed = window.confirm(`Delete ${member.full_name}? This will remove access for this portal user.`);
    if (!confirmed) return;
    try {
      setSaving(true);
      await tenantAdminApi.deleteMember(member.id);
      await loadMembers();
      setPendingDelete(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete portal user.");
    } finally {
      setSaving(false);
    }
  }

  const activeCount = members.filter((member) => member.is_active && member.status === "active").length;
  const adminCount = members.filter((member) => member.role === "TENANT_ADMIN").length;
  const userCount = members.filter((member) => member.role === "TENANT_USER").length;

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Portal users</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Portal Users in {currentTenant?.name ?? "your tenant"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              This page is scoped to the logged-in tenant only. Tenant admins can create, edit, suspend, and remove portal users without accessing other tenants.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadMembers()} disabled={refreshing}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Create Portal User
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Total Portal Users</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{members.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tenant Admins</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{adminCount}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Users</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{userCount}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Active Portal Users</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{activeCount}</div>
        </Card>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-slate-950/75 lg:grid-cols-[1fr_auto] lg:items-end">
        <Input label="Search portal users" placeholder="Name, email, role, status" value={search} onChange={(event) => setSearch(event.target.value)} leftIcon={<Search className="h-4 w-4" />} />
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
          Only portal users from the current tenant are shown here.
        </div>
      </section>

      <DataTable
        title="Portal user list"
        subtitle="Name, Email, Role, Status, Created Date, Actions"
        headers={["Name", "Email", "Role", "Status", "Created Date", "Actions"]}
        emptyState={
          !loading && filteredMembers.length === 0 ? (
            <div className="px-5 py-10 text-center text-sm text-slate-500 dark:text-slate-400">No portal users found for the current filters.</div>
          ) : null
        }
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={6}>
              Loading portal users...
            </td>
          </tr>
        ) : (
          visibleMembers.map((member) => (
            <tr key={member.id}>
              <td className="px-5 py-4">
                <div className="font-medium text-slate-900 dark:text-white">{member.full_name}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{member.id}</div>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{member.email}</td>
              <td className="px-5 py-4"><Badge tone="info">{roleLabel(member.role)}</Badge></td>
              <td className="px-5 py-4"><Badge tone={statusTone(member.status)}>{member.status}</Badge></td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatDate(member.created_at)}</td>
              <td className="px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" leftIcon={<PencilLine className="h-4 w-4" />} onClick={() => void openEdit(member)}>
                    Edit
                  </Button>
                  <Button variant="secondary" size="sm" leftIcon={<UserRoundCog className="h-4 w-4" />} onClick={() => setPendingDelete(member)}>
                    Suspend/Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))
        )}
      </DataTable>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-slate-500 dark:text-slate-400">
          Showing {filteredMembers.length === 0 ? 0 : (page - 1) * pageSize + 1} to {filteredMembers.length === 0 ? 0 : Math.min(page * pageSize, filteredMembers.length)} of {filteredMembers.length} portal users
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page === 1}>
            Previous
          </Button>
          <Button variant="secondary" size="sm" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page === totalPages}>
            Next
          </Button>
        </div>
      </div>

      <Modal
        open={mode !== null}
        title={mode === "create" ? "Create portal user" : "Edit portal user"}
        description="Edit the portal user inside a pop-up form without leaving the tenant admin workspace."
        onClose={closeModal}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" form="tenant-admin-member-form" disabled={saving || (mode === "edit" && !activeMember)}>
              {saving ? "Saving..." : mode === "create" ? "Create portal user" : "Save changes"}
            </Button>
          </div>
        }
      >
        <form id="tenant-admin-member-form" onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Name" value={draft.full_name} onChange={(event) => setDraft((current) => ({ ...current, full_name: event.target.value }))} />
            <Input label="Email" type="email" value={draft.email} onChange={(event) => setDraft((current) => ({ ...current, email: event.target.value }))} />
            <Input
              label="Password"
              type="password"
              value={draft.password}
              onChange={(event) => setDraft((current) => ({ ...current, password: event.target.value }))}
              helpText={mode === "edit" ? "Leave blank to keep the current password." : undefined}
            />
            <label className="grid gap-2">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Role</span>
              <select
                value={draft.role}
                onChange={(event) => setDraft((current) => ({ ...current, role: event.target.value as Draft["role"] }))}
                className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100"
              >
                <option value="tenant_admin">tenant_admin</option>
                <option value="user">user</option>
              </select>
            </label>
            <label className="grid gap-2 md:col-span-2">
              <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Status</span>
              <select
                value={draft.status}
                onChange={(event) => setDraft((current) => ({ ...current, status: event.target.value as Draft["status"] }))}
                className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100"
              >
                <option value="active">active</option>
                <option value="inactive">inactive</option>
                <option value="suspended">suspended</option>
              </select>
            </label>
          </div>

          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Assigned features</span>
            <div className="rounded-2xl border border-slate-200 bg-white/90 p-4 shadow-sm dark:border-white/10 dark:bg-slate-950/70">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-xs uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Assigned features</p>
                <Badge tone="info">{selectedFeatureCodes.length} selected</Badge>
              </div>
              <div className="mt-4 grid gap-3">
                {featureOptions.length === 0 ? (
                  <div className="rounded-xl border border-dashed border-slate-200 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:text-slate-400">
                    No tenant-enabled optional features are available.
                  </div>
                ) : null}
                {featureOptions.map((feature) => {
                  const checked = selectedFeatureCodes.includes(feature.feature_code);
                  return (
                    <label
                      key={feature.feature_code}
                      className="flex cursor-pointer items-start gap-3 rounded-2xl border border-slate-200 px-4 py-3 transition hover:border-brand-400/50 hover:bg-brand-50/40 dark:border-white/10 dark:hover:border-brand-400/40 dark:hover:bg-white/5"
                    >
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(event) => {
                          const next = event.target.checked
                            ? Array.from(new Set([...selectedFeatureCodes, feature.feature_code]))
                            : selectedFeatureCodes.filter((code) => code !== feature.feature_code);
                          setSelectedFeatureCodes(next);
                        }}
                        className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-500 focus:ring-brand-400"
                      />
                      <span className="grid gap-1">
                        <span className="font-medium text-slate-900 dark:text-white">{feature.feature_name}</span>
                        <span className="text-xs text-slate-500 dark:text-slate-400">{feature.feature_code}</span>
                      </span>
                    </label>
                  );
                })}
              </div>
              {!selectedFeatureCodes.length ? (
                <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">No optional features assigned.</p>
              ) : (
                <div className="mt-4 flex flex-wrap gap-2">
                  {selectedFeatureCodes.map((code) => {
                    const feature = featureOptions.find((item) => item.feature_code === code);
                    return (
                      <Badge key={code} tone="success">
                        {feature?.feature_name ?? code}
                      </Badge>
                    );
                  })}
                </div>
              )}
            </div>
          </label>
        </form>
      </Modal>

      <Modal
        open={pendingDelete !== null}
        title="Suspend or delete portal user"
        description="Choose whether to suspend the account or remove access completely."
        onClose={() => setPendingDelete(null)}
        footer={
          <div className="flex flex-wrap justify-end gap-2">
            <Button variant="secondary" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="secondary"
              onClick={async () => {
                if (!pendingDelete) return;
                try {
                  setSaving(true);
                  await tenantAdminApi.updateMember(pendingDelete.id, { status: "suspended" });
                  await loadMembers();
                  setPendingDelete(null);
                } catch (err) {
                  setError(err instanceof Error ? err.message : "Unable to suspend portal user.");
                } finally {
                  setSaving(false);
                }
              }}
              disabled={saving || !pendingDelete}
            >
              Suspend
            </Button>
            <Button variant="danger" onClick={() => pendingDelete && void handleDelete(pendingDelete)} disabled={saving || !pendingDelete}>
              Delete
            </Button>
          </div>
        }
      >
        <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">
          Suspending keeps the account in the tenant but disables access. Deleting will soft-remove the portal user from the tenant.
        </p>
      </Modal>
    </div>
  );
}

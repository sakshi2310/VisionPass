import { Plus, Save, Trash2, Users as UsersIcon } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useApp } from "@/context/AppContext";
import { adminApi, type AdminTenantUser } from "@/services/admin";

type UserDraft = {
  id?: string;
  fullName: string;
  email: string;
  password: string;
  role: "TENANT_ADMIN" | "TENANT_USER";
  isActive: boolean;
};

const emptyDraft: UserDraft = {
  fullName: "",
  email: "",
  password: "",
  role: "TENANT_USER",
  isActive: true,
};

export function Users() {
  const { user } = useApp();
  const [users, setUsers] = useState<AdminTenantUser[]>([]);
  const [draft, setDraft] = useState<UserDraft>(emptyDraft);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const canManage = user?.role === "TENANT_ADMIN" || user?.role === "CLIENT_ADMIN" || user?.role === "SUPER_ADMIN";

  useEffect(() => {
    let active = true;

    async function loadUsers() {
      try {
        setLoading(true);
        const data = await adminApi.listTenantUsers();
        if (!active) return;
        setUsers(data);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unable to load users.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadUsers();

    return () => {
      active = false;
    };
  }, []);

  const selectedUser = useMemo(() => users.find((item) => item.id === draft.id) ?? null, [draft.id, users]);

  function resetDraft() {
    setDraft(emptyDraft);
    setError("");
    setSuccess("");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canManage) return;
    if (!draft.fullName.trim() || !draft.email.trim()) {
      setError("Full name and email are required.");
      return;
    }
    if (!draft.id && !draft.password.trim()) {
      setError("Password is required for new users.");
      return;
    }

    setSaving(true);
    setError("");
    setSuccess("");
    try {
      if (draft.id) {
        const updated = await adminApi.updateTenantUser(draft.id, {
          full_name: draft.fullName,
          email: draft.email,
          password: draft.password || undefined,
          role: draft.role,
          is_active: draft.isActive,
        });
        setUsers((current) => current.map((item) => (item.id === updated.id ? updated : item)));
        setSuccess("User updated.");
      } else {
        const created = await adminApi.createTenantUser({
          full_name: draft.fullName,
          email: draft.email,
          password: draft.password,
          role: draft.role,
          is_active: draft.isActive,
        });
        setUsers((current) => [created, ...current]);
        setSuccess("User created.");
      }
      resetDraft();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save user.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(userId: string) {
    if (!canManage) return;
    try {
      await adminApi.deleteTenantUser(userId);
      setUsers((current) => current.filter((item) => item.id !== userId));
      if (draft.id === userId) resetDraft();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete user.");
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Tenant users</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Manage users in this tenant</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Add, edit, disable, or remove users for the current organization. Passwords are optional on edit, but required on create.
        </p>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}
      {success ? <div className="rounded-2xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">{success}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="grid gap-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">User form</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Create a tenant user or update an existing one.</p>
            </div>
            <Badge tone="neutral">{selectedUser ? "editing" : "new"}</Badge>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-4">
            <div className="grid gap-3 md:grid-cols-2">
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Full name</span>
                <input className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white" value={draft.fullName} onChange={(event) => setDraft((current) => ({ ...current, fullName: event.target.value }))} />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Email</span>
                <input className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white" value={draft.email} onChange={(event) => setDraft((current) => ({ ...current, email: event.target.value }))} />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Password {draft.id ? "(optional)" : ""}</span>
                <input type="password" className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white" value={draft.password} onChange={(event) => setDraft((current) => ({ ...current, password: event.target.value }))} />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Role</span>
                <select className="h-11 rounded-2xl border border-slate-200 bg-white px-4 text-slate-900 outline-none dark:border-white/10 dark:bg-slate-950/70 dark:text-white" value={draft.role} onChange={(event) => setDraft((current) => ({ ...current, role: event.target.value as UserDraft["role"] }))}>
                  <option value="TENANT_USER">Tenant user</option>
                  <option value="TENANT_ADMIN">Tenant admin</option>
                </select>
              </label>
            </div>

            <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-sm text-slate-300">
              <input type="checkbox" checked={draft.isActive} onChange={(event) => setDraft((current) => ({ ...current, isActive: event.target.checked }))} />
              Active account
            </label>

            <div className="flex gap-3">
              <Button type="button" variant="secondary" className="w-full" onClick={resetDraft}>
                Clear
              </Button>
              <Button type="submit" className="w-full" leftIcon={draft.id ? <Save className="h-4 w-4" /> : <Plus className="h-4 w-4" />} disabled={saving}>
                {saving ? "Saving..." : draft.id ? "Update user" : "Create user"}
              </Button>
            </div>
          </form>
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Users</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Current tenant members.</p>
            </div>
            <UsersIcon className="h-5 w-5 text-cyan-400" />
          </div>

          {loading ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">Loading users...</p>
          ) : (
            <div className="grid gap-3">
              {users.map((item) => (
                <div key={item.id} className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{item.name}</div>
                      <div className="text-sm text-slate-500 dark:text-slate-400">{item.email}</div>
                      <div className="mt-2 flex flex-wrap gap-2">
                        <Badge tone="info">{item.role}</Badge>
                        <Badge tone={item.isActive ? "success" : "neutral"}>{item.isActive ? "active" : "inactive"}</Badge>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="secondary"
                        onClick={() =>
                          setDraft({
                            id: item.id,
                            fullName: item.name,
                            email: item.email,
                            password: "",
                            role: item.role === "TENANT_ADMIN" ? "TENANT_ADMIN" : "TENANT_USER",
                            isActive: item.isActive,
                          })
                        }
                      >
                        Edit
                      </Button>
                      <Button variant="secondary" onClick={() => handleDelete(item.id)} leftIcon={<Trash2 className="h-4 w-4" />}>
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
}

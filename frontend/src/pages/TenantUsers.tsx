import { Eye, PencilLine, Plus, Power, Trash2, Users2 } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { useApp } from "@/context/AppContext";
import { formatDate } from "@/utils/format";
import { tenantUsersApi, type TenantUserRecord } from "@/services/tenantUsers";
import { TenantUserModal } from "@/pages/TenantUserModal";

type ModalMode = "create" | "edit" | "view";

function roleLabel(role: string) {
  switch (role) {
    case "TENANT_USER":
      return "tenant_user";
    case "SECURITY_GUARD":
      return "security_guard";
    case "RECEPTIONIST":
      return "receptionist";
    case "ATTENDANCE_OPERATOR":
      return "attendance_operator";
    case "CAMERA_OPERATOR":
      return "camera_operator";
    case "MANAGER":
      return "manager";
    default:
      return role.toLowerCase();
  }
}

export function TenantUsers() {
  const { currentTenant } = useApp();
  const [users, setUsers] = useState<TenantUserRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<ModalMode>("create");
  const [activeUser, setActiveUser] = useState<TenantUserRecord | null>(null);

  async function loadUsers() {
    try {
      setLoading(true);
      setError("");
      const data = await tenantUsersApi.list();
      setUsers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load users.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadUsers();
  }, []);

  const activeCount = useMemo(() => users.filter((user) => user.isActive && !user.isDeleted).length, [users]);
  const faceCount = useMemo(() => users.filter((user) => user.faceEnrolled && !user.isDeleted).length, [users]);

  function openModal(mode: ModalMode, user: TenantUserRecord | null = null) {
    setModalMode(mode);
    setActiveUser(user);
    setModalOpen(true);
  }

  async function handleSubmit(payload: {
    full_name: string;
    email: string;
    password: string;
    phone?: string | null;
    role: string;
    department?: string | null;
    designation?: string | null;
    employee_id?: string | null;
    access_zones?: string[];
    is_active?: boolean;
    face_enrolled?: boolean;
    notes?: string | null;
  }) {
    try {
      setSaving(true);
      if (modalMode === "create") {
        await tenantUsersApi.create(payload);
      } else if (modalMode === "edit" && activeUser) {
        await tenantUsersApi.update(activeUser.id, payload);
      }
      setModalOpen(false);
      setActiveUser(null);
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to save user.");
    } finally {
      setSaving(false);
    }
  }

  async function toggleStatus(user: TenantUserRecord) {
    try {
      setSaving(true);
      await tenantUsersApi.updateStatus(user.id, { is_active: !user.isActive, face_enrolled: user.faceEnrolled });
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update status.");
    } finally {
      setSaving(false);
    }
  }

  async function removeUser(user: TenantUserRecord) {
    if (!window.confirm(`Delete ${user.fullName}? This will soft delete the account.`)) return;
    try {
      setSaving(true);
      await tenantUsersApi.remove(user.id);
      await loadUsers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to delete user.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Tenant users</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Manage users inside {currentTenant?.name ?? "this tenant"}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Create tenant users, update their status, and keep every record scoped to the logged-in tenant only.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Total users</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{users.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Active users</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{activeCount}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Face enrolled</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{faceCount}</div>
        </Card>
      </div>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <Card className="p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Tenant user list</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Full Name, Email, Phone, Role, Status, Face Enrolled, Created Date, Actions</p>
          </div>
          <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => openModal("create")}>
            Add tenant user
          </Button>
        </div>

        <DataTable
          headers={["Full Name", "Email", "Phone", "Role", "Status", "Face Enrolled", "Created Date", "Actions"]}
          emptyState={
            !loading && users.length === 0 ? (
              <div className="px-5 py-10 text-center text-sm text-slate-500 dark:text-slate-400">No tenant users yet.</div>
            ) : null
          }
        >
          {loading ? (
            <tr>
              <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={8}>Loading users...</td>
            </tr>
          ) : (
            users.map((user) => (
              <tr key={user.id}>
                <td className="px-5 py-4">
                  <div className="font-medium text-slate-900 dark:text-white">{user.fullName}</div>
                  <div className="text-xs text-slate-500 dark:text-slate-400">{user.department ?? "-"}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{user.email}</td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{user.phone ?? "-"}</td>
                <td className="px-5 py-4"><Badge tone="info">{roleLabel(user.role)}</Badge></td>
                <td className="px-5 py-4">
                  <Badge tone={user.isActive ? "success" : "danger"}>{user.isActive ? "Active" : "Inactive"}</Badge>
                </td>
                <td className="px-5 py-4">
                  <Badge tone={user.faceEnrolled ? "success" : "neutral"}>{user.faceEnrolled ? "Yes" : "No"}</Badge>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatDate(user.createdAt)}</td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => openModal("view", user)}>View</Button>
                    <Button variant="secondary" size="sm" leftIcon={<PencilLine className="h-4 w-4" />} onClick={() => openModal("edit", user)}>Edit</Button>
                    <Button variant="secondary" size="sm" leftIcon={<Power className="h-4 w-4" />} onClick={() => void toggleStatus(user)} disabled={saving}>
                      {user.isActive ? "Deactivate" : "Activate"}
                    </Button>
                    <Button variant="danger" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void removeUser(user)} disabled={saving}>Delete</Button>
                  </div>
                </td>
              </tr>
            ))
          )}
        </DataTable>
      </Card>

      <TenantUserModal
        open={modalOpen}
        mode={modalMode}
        user={activeUser}
        saving={saving}
        onClose={() => setModalOpen(false)}
        onSubmit={handleSubmit}
      />
    </div>
  );
}
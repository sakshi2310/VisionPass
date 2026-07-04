import { CalendarDays, Plus, RefreshCw, Save, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { formatDate } from "@/utils/format";
import {
  createHoliday,
  deleteHoliday,
  fetchHolidays,
  updateHoliday,
  type AttendanceHoliday,
  type AttendanceHolidayPayload,
} from "@/services/clientAdminAttendance";

type Mode = "create" | "edit";

type Draft = {
  holiday_name: string;
  holiday_date: string;
  department_id: string;
  location_id: string;
  is_active: boolean;
};

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

const defaultDraft: Draft = {
  holiday_name: "",
  holiday_date: "",
  department_id: "",
  location_id: "",
  is_active: true,
};

function fromHoliday(holiday: AttendanceHoliday): Draft {
  return {
    holiday_name: holiday.holiday_name,
    holiday_date: holiday.holiday_date,
    department_id: holiday.department_id ?? "",
    location_id: holiday.location_id ?? "",
    is_active: holiday.is_active,
  };
}

function toPayload(draft: Draft): AttendanceHolidayPayload {
  return {
    holiday_name: draft.holiday_name.trim(),
    holiday_date: draft.holiday_date,
    department_id: draft.department_id.trim() || null,
    location_id: draft.location_id.trim() || null,
    is_active: draft.is_active,
  };
}

function validateDraft(draft: Draft) {
  if (!draft.holiday_name.trim()) return "Holiday name is required.";
  if (!draft.holiday_date.trim()) return "Holiday date is required.";
  return "";
}

export function AttendanceHolidaysPage() {
  const { currentTenant } = useApp();
  const [holidays, setHolidays] = useState<AttendanceHoliday[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<ToastState>(null);
  const [mode, setMode] = useState<Mode | null>(null);
  const [activeHoliday, setActiveHoliday] = useState<AttendanceHoliday | null>(null);
  const [draft, setDraft] = useState<Draft>(defaultDraft);

  usePageTitle("Vision Pass | Holiday Management");

  async function loadHolidays(showRefreshing = false) {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError("");
      const response = await fetchHolidays();
      setHolidays(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load holidays.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadHolidays();
  }, []);

  const upcomingCount = useMemo(() => {
    const today = new Date().toISOString().slice(0, 10);
    return holidays.filter((holiday) => holiday.holiday_date >= today).length;
  }, [holidays]);

  function openCreate() {
    setMode("create");
    setActiveHoliday(null);
    setDraft(defaultDraft);
    setError("");
  }

  function openEdit(holiday: AttendanceHoliday) {
    setMode("edit");
    setActiveHoliday(holiday);
    setDraft(fromHoliday(holiday));
    setError("");
  }

  function closeModal() {
    setMode(null);
    setActiveHoliday(null);
    setDraft(defaultDraft);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationMessage = validateDraft(draft);
    if (validationMessage) {
      setToast({ tone: "error", title: "Validation error", message: validationMessage });
      return;
    }

    try {
      setSaving(true);
      setError("");
      const payload = toPayload(draft);
      if (mode === "create") {
        await createHoliday(payload);
        setToast({ tone: "success", title: "Holiday created", message: "The holiday was added for this tenant." });
      } else if (mode === "edit" && activeHoliday) {
        await updateHoliday(activeHoliday.id, payload);
        setToast({ tone: "success", title: "Holiday updated", message: "The holiday was saved successfully." });
      }
      closeModal();
      await loadHolidays(true);
    } catch (err) {
      setToast({ tone: "error", title: "Save failed", message: err instanceof Error ? err.message : "Unable to save holiday." });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(holiday: AttendanceHoliday) {
    const confirmed = window.confirm(`Delete ${holiday.holiday_name}? This action cannot be undone.`);
    if (!confirmed) return;
    try {
      setSaving(true);
      await deleteHoliday(holiday.id);
      await loadHolidays(true);
      setToast({ tone: "success", title: "Holiday deleted", message: `${holiday.holiday_name} was removed from this tenant.` });
    } catch (err) {
      setToast({ tone: "error", title: "Delete failed", message: err instanceof Error ? err.message : "Unable to delete holiday." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Holiday management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Manage tenant holidays</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Add, edit, and remove tenant holidays. Upcoming holidays appear first and every record stays isolated to the current tenant.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadHolidays(true)} disabled={refreshing || saving}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate} disabled={saving}>
              Add holiday
            </Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Total holidays</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{holidays.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Upcoming holidays</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{upcomingCount}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Active holidays</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{holidays.filter((holiday) => holiday.is_active).length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tenant</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{currentTenant?.name ?? "Current tenant"}</div>
        </Card>
      </section>

      <DataTable
        title="Holiday list"
        subtitle="Name, Date, Scope, Status, Actions"
        headers={["Name", "Date", "Scope", "Status", "Actions"]}
        emptyState={!loading && holidays.length === 0 ? <EmptyState title="No holidays yet" description="Add the first holiday for this tenant to start tracking closures and exceptions." action={<Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>Add holiday</Button>} /> : null}
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={5}>
              Loading holidays...
            </td>
          </tr>
        ) : (
          holidays.map((holiday) => (
            <tr key={holiday.id}>
              <td className="px-5 py-4">
                <div className="font-medium text-slate-900 dark:text-white">{holiday.holiday_name}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{holiday.id}</div>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatDate(holiday.holiday_date)}</td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                <div>{holiday.department_id ? `Department: ${holiday.department_id}` : "All departments"}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{holiday.location_id ? `Location: ${holiday.location_id}` : "All locations"}</div>
              </td>
              <td className="px-5 py-4">
                <Badge tone={holiday.is_active ? "success" : "neutral"}>{holiday.is_active ? "Active" : "Inactive"}</Badge>
              </td>
              <td className="px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" leftIcon={<CalendarDays className="h-4 w-4" />} onClick={() => openEdit(holiday)}>
                    Edit
                  </Button>
                  <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void handleDelete(holiday)} disabled={saving}>
                    Delete
                  </Button>
                </div>
              </td>
            </tr>
          ))
        )}
      </DataTable>

      <Modal
        open={mode !== null}
        title={mode === "create" ? "Add holiday" : "Edit holiday"}
        description="Create or update a tenant-specific holiday record."
        onClose={closeModal}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" form="attendance-holiday-form" leftIcon={<Save className="h-4 w-4" />} disabled={saving}>
              {saving ? "Saving..." : mode === "create" ? "Create holiday" : "Save holiday"}
            </Button>
          </div>
        }
      >
        <form id="attendance-holiday-form" onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Holiday name" value={draft.holiday_name} onChange={(event) => setDraft((current) => ({ ...current, holiday_name: event.target.value }))} />
            <Input label="Holiday date" type="date" value={draft.holiday_date} onChange={(event) => setDraft((current) => ({ ...current, holiday_date: event.target.value }))} />
            <Input label="Department (optional)" value={draft.department_id} onChange={(event) => setDraft((current) => ({ ...current, department_id: event.target.value }))} />
            <Input label="Location (optional)" value={draft.location_id} onChange={(event) => setDraft((current) => ({ ...current, location_id: event.target.value }))} />
          </div>

          <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
            <input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft((current) => ({ ...current, is_active: event.target.checked }))} />
            Active holiday
          </label>
        </form>
      </Modal>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} icon={<CalendarDays className="h-5 w-5" />} />
        </div>
      ) : null}
    </div>
  );
}


import { CalendarClock, CheckCircle2, Plus, RefreshCw, Save, Trash2 } from "lucide-react";
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
import { formatTime } from "@/utils/format";
import {
  createShift,
  deleteShift,
  fetchShifts,
  setDefaultShift,
  updateShift,
  type AttendanceShift,
  type AttendanceShiftPayload,
} from "@/services/clientAdminAttendance";

type Mode = "create" | "edit";

type Draft = {
  name: string;
  start_time: string;
  end_time: string;
  grace_period_minutes: string;
  late_after_minutes: string;
  half_day_min_minutes: string;
  full_day_min_minutes: string;
  auto_checkout_time: string;
  break_duration_minutes: string;
  is_default: boolean;
  is_active: boolean;
};

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

const defaultDraft: Draft = {
  name: "General Shift",
  start_time: "09:30",
  end_time: "18:30",
  grace_period_minutes: "10",
  late_after_minutes: "10",
  half_day_min_minutes: "240",
  full_day_min_minutes: "480",
  auto_checkout_time: "19:00",
  break_duration_minutes: "60",
  is_default: false,
  is_active: true,
};

function shiftFormToPayload(draft: Draft): AttendanceShiftPayload {
  return {
    name: draft.name.trim(),
    start_time: draft.start_time,
    end_time: draft.end_time,
    grace_period_minutes: Number(draft.grace_period_minutes),
    late_after_minutes: Number(draft.late_after_minutes),
    half_day_min_minutes: Number(draft.half_day_min_minutes),
    full_day_min_minutes: Number(draft.full_day_min_minutes),
    auto_checkout_time: draft.auto_checkout_time.trim() || null,
    break_duration_minutes: Number(draft.break_duration_minutes),
    is_default: draft.is_default,
    is_active: draft.is_active,
  };
}

function fromShift(shift: AttendanceShift): Draft {
  return {
    name: shift.name,
    start_time: shift.start_time.slice(0, 5),
    end_time: shift.end_time.slice(0, 5),
    grace_period_minutes: String(shift.grace_period_minutes),
    late_after_minutes: String(shift.late_after_minutes),
    half_day_min_minutes: String(shift.half_day_min_minutes),
    full_day_min_minutes: String(shift.full_day_min_minutes),
    auto_checkout_time: shift.auto_checkout_time ? shift.auto_checkout_time.slice(0, 5) : "",
    break_duration_minutes: String(shift.break_duration_minutes),
    is_default: shift.is_default,
    is_active: shift.is_active,
  };
}

function validateDraft(draft: Draft) {
  if (!draft.name.trim()) return "Shift name is required.";
  if (!draft.start_time.trim()) return "Start time is required.";
  if (!draft.end_time.trim()) return "End time is required.";
  const grace = Number(draft.grace_period_minutes);
  const lateAfter = Number(draft.late_after_minutes);
  const halfDay = Number(draft.half_day_min_minutes);
  const fullDay = Number(draft.full_day_min_minutes);
  const breakMinutes = Number(draft.break_duration_minutes);
  if (Number.isNaN(grace) || grace < 0) return "Grace period cannot be negative.";
  if (Number.isNaN(lateAfter) || lateAfter < 0) return "Late after minutes cannot be negative.";
  if (Number.isNaN(halfDay) || halfDay < 1) return "Half day minimum minutes must be at least 1.";
  if (Number.isNaN(fullDay) || fullDay < 1) return "Full day minimum minutes must be at least 1.";
  if (fullDay <= halfDay) return "Full day minimum minutes must be greater than half day minimum minutes.";
  if (Number.isNaN(breakMinutes) || breakMinutes < 0) return "Break duration cannot be negative.";
  return "";
}

export function AttendanceShiftsPage() {
  const { currentTenant } = useApp();
  const [shifts, setShifts] = useState<AttendanceShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<ToastState>(null);
  const [mode, setMode] = useState<Mode | null>(null);
  const [activeShift, setActiveShift] = useState<AttendanceShift | null>(null);
  const [draft, setDraft] = useState<Draft>(defaultDraft);

  usePageTitle("Vision Pass | Shift Management");

  async function loadShifts(showRefreshing = false) {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError("");
      const response = await fetchShifts();
      setShifts(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load shifts.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadShifts();
  }, []);

  const defaultShift = useMemo(() => shifts.find((shift) => shift.is_default) ?? null, [shifts]);

  function openCreate() {
    setMode("create");
    setActiveShift(null);
    setDraft(defaultDraft);
    setError("");
  }

  function openEdit(shift: AttendanceShift) {
    setMode("edit");
    setActiveShift(shift);
    setDraft(fromShift(shift));
    setError("");
  }

  function closeModal() {
    setMode(null);
    setActiveShift(null);
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
      const payload = shiftFormToPayload(draft);
      if (mode === "create") {
        await createShift(payload);
        setToast({ tone: "success", title: "Shift created", message: "The new shift was added for this tenant." });
      } else if (mode === "edit" && activeShift) {
        await updateShift(activeShift.id, payload);
        setToast({ tone: "success", title: "Shift updated", message: "The shift was saved successfully." });
      }
      closeModal();
      await loadShifts(true);
    } catch (err) {
      setToast({ tone: "error", title: "Save failed", message: err instanceof Error ? err.message : "Unable to save shift." });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(shift: AttendanceShift) {
    const confirmed = window.confirm(`Delete ${shift.name}? This action cannot be undone.`);
    if (!confirmed) return;
    try {
      setSaving(true);
      await deleteShift(shift.id);
      await loadShifts(true);
      setToast({ tone: "success", title: "Shift deleted", message: `${shift.name} was removed from this tenant.` });
    } catch (err) {
      setToast({ tone: "error", title: "Delete failed", message: err instanceof Error ? err.message : "Unable to delete shift." });
    } finally {
      setSaving(false);
    }
  }

  async function handleSetDefault(shift: AttendanceShift) {
    try {
      setSaving(true);
      await setDefaultShift(shift.id);
      await loadShifts(true);
      setToast({ tone: "success", title: "Default shift updated", message: `${shift.name} is now the default shift.` });
    } catch (err) {
      setToast({ tone: "error", title: "Update failed", message: err instanceof Error ? err.message : "Unable to set default shift." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Shift management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Manage tenant shifts</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Add, edit, delete, and default shifts for the active tenant. Every record is filtered by tenant_id on the backend.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadShifts(true)} disabled={refreshing || saving}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate} disabled={saving}>
              Add shift
            </Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Total shifts</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{shifts.length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Default shift</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{defaultShift?.name ?? "None"}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Active shifts</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{shifts.filter((shift) => shift.is_active).length}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Tenant</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{currentTenant?.name ?? "Current tenant"}</div>
        </Card>
      </section>

      <DataTable
        title="Shift list"
        subtitle="Name, Time Window, Grace, Break, Default, Status, Actions"
        headers={["Name", "Time Window", "Grace", "Break", "Default", "Status", "Actions"]}
        emptyState={!loading && shifts.length === 0 ? <EmptyState title="No shifts yet" description="Create the first shift for this tenant to start scheduling attendance." action={<Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>Add shift</Button>} /> : null}
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={7}>
              Loading shifts...
            </td>
          </tr>
        ) : (
          shifts.map((shift) => (
            <tr key={shift.id}>
              <td className="px-5 py-4">
                <div className="font-medium text-slate-900 dark:text-white">{shift.name}</div>
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{shift.id}</div>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                {formatTime(`1970-01-01T${shift.start_time}`)} - {formatTime(`1970-01-01T${shift.end_time}`)}
                <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">Auto checkout: {shift.auto_checkout_time ? formatTime(`1970-01-01T${shift.auto_checkout_time}`) : "N/A"}</div>
              </td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{shift.grace_period_minutes} / {shift.late_after_minutes}</td>
              <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{shift.break_duration_minutes} min</td>
              <td className="px-5 py-4">
                {shift.is_default ? <Badge tone="success">Default</Badge> : <Badge tone="neutral">Standard</Badge>}
              </td>
              <td className="px-5 py-4">
                <Badge tone={shift.is_active ? "success" : "neutral"}>{shift.is_active ? "Active" : "Inactive"}</Badge>
              </td>
              <td className="px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" leftIcon={<CalendarClock className="h-4 w-4" />} onClick={() => openEdit(shift)}>
                    Edit
                  </Button>
                  <Button variant="secondary" size="sm" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => void handleSetDefault(shift)} disabled={shift.is_default || saving}>
                    Set Default
                  </Button>
                  <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void handleDelete(shift)} disabled={saving}>
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
        title={mode === "create" ? "Add shift" : "Edit shift"}
        description="Create or update a tenant-specific attendance shift."
        onClose={closeModal}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button type="submit" form="attendance-shift-form" leftIcon={<Save className="h-4 w-4" />} disabled={saving}>
              {saving ? "Saving..." : mode === "create" ? "Create shift" : "Save shift"}
            </Button>
          </div>
        }
      >
        <form id="attendance-shift-form" onSubmit={handleSubmit} className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            <Input label="Shift name" value={draft.name} onChange={(event) => setDraft((current) => ({ ...current, name: event.target.value }))} />
            <Input label="Start time" type="time" value={draft.start_time} onChange={(event) => setDraft((current) => ({ ...current, start_time: event.target.value }))} />
            <Input label="End time" type="time" value={draft.end_time} onChange={(event) => setDraft((current) => ({ ...current, end_time: event.target.value }))} />
            <Input label="Auto checkout time" type="time" value={draft.auto_checkout_time} onChange={(event) => setDraft((current) => ({ ...current, auto_checkout_time: event.target.value }))} />
            <Input label="Grace period minutes" type="number" min={0} value={draft.grace_period_minutes} onChange={(event) => setDraft((current) => ({ ...current, grace_period_minutes: event.target.value }))} />
            <Input label="Late after minutes" type="number" min={0} value={draft.late_after_minutes} onChange={(event) => setDraft((current) => ({ ...current, late_after_minutes: event.target.value }))} />
            <Input label="Half day minimum minutes" type="number" min={1} value={draft.half_day_min_minutes} onChange={(event) => setDraft((current) => ({ ...current, half_day_min_minutes: event.target.value }))} />
            <Input label="Full day minimum minutes" type="number" min={1} value={draft.full_day_min_minutes} onChange={(event) => setDraft((current) => ({ ...current, full_day_min_minutes: event.target.value }))} />
            <Input label="Break duration minutes" type="number" min={0} value={draft.break_duration_minutes} onChange={(event) => setDraft((current) => ({ ...current, break_duration_minutes: event.target.value }))} />
          </div>

          <div className="grid gap-3 md:grid-cols-2">
            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
              <input type="checkbox" checked={draft.is_default} onChange={(event) => setDraft((current) => ({ ...current, is_default: event.target.checked }))} />
              Set as default shift
            </label>
            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
              <input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft((current) => ({ ...current, is_active: event.target.checked }))} />
              Active shift
            </label>
          </div>
        </form>
      </Modal>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} icon={<CalendarClock className="h-5 w-5" />} />
        </div>
      ) : null}
    </div>
  );
}

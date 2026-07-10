import { ImagePlus, Loader2, Pencil, Plus, PowerOff, Power, RefreshCw, Save, ScanFace, Trash2, Upload, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import type { Employee, EmployeePayload, EmployeeFaceProfile } from "@/services/clientAdminAttendance";
import { staffApi } from "@/services/staff";
import { formatDate } from "@/utils/format";

type Draft = {
  employee_code: string;
  full_name: string;
  email: string;
  mobile: string;
  department: string;
  designation: string;
  joining_date: string;
  is_active: boolean;
};

type FaceProfileMap = Record<string, EmployeeFaceProfile | null>;

type FormErrors = Partial<Record<"full_name" | "email" | "faceFiles", string>>;

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

const emptyDraft: Draft = {
  employee_code: "",
  full_name: "",
  email: "",
  mobile: "",
  department: "",
  designation: "",
  joining_date: "",
  is_active: true,
};

function todayLocal() {
  const now = new Date();
  return new Date(now.getTime() - now.getTimezoneOffset() * 60_000).toISOString().slice(0, 10);
}

function toPayload(draft: Draft): EmployeePayload {
  return {
    employee_code: draft.employee_code.trim() || undefined,
    full_name: draft.full_name.trim(),
    email: draft.email.trim(),
    mobile: draft.mobile.trim() || null,
    gender: null,
    date_of_birth: null,
    department: draft.department.trim() || null,
    designation: draft.designation.trim() || null,
    shift_id: null,
    joining_date: draft.joining_date || null,
    employee_type: "Full Time",
    is_active: draft.is_active,
  };
}

function fromEmployee(employee: Employee): Draft {
  return {
    employee_code: employee.employee_code,
    full_name: employee.full_name,
    email: employee.email,
    mobile: employee.mobile ?? "",
    department: employee.department ?? "",
    designation: employee.designation ?? "",
    joining_date: employee.joining_date ?? "",
    is_active: employee.is_active,
  };
}

function faceTone(status?: string | null) {
  if (status === "Enrolled") return "success" as const;
  if (status === "Processing") return "warning" as const;
  if (status === "Failed") return "danger" as const;
  return "neutral" as const;
}

function faceLabel(profile?: EmployeeFaceProfile | null) {
  if (!profile) return "Not Enrolled";
  return profile.enrollment_status || "Not Enrolled";
}

export function StaffPage() {
  const [items, setItems] = useState<Employee[]>([]);
  const [profiles, setProfiles] = useState<FaceProfileMap>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [mode, setMode] = useState<"create" | "edit">("create");
  const [activeItem, setActiveItem] = useState<Employee | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [faceFiles, setFaceFiles] = useState<File[]>([]);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [formError, setFormError] = useState("");
  const [toast, setToast] = useState<ToastState>(null);

  const facePreviews = useMemo(
    () => faceFiles.map((file) => ({ file, url: URL.createObjectURL(file) })),
    [faceFiles],
  );

  usePageTitle("Vision Pass | Staff");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const staffRows = await staffApi.list({
        search: search.trim() || undefined,
      });
      setItems(staffRows);
      const nextProfiles: FaceProfileMap = {};
      await Promise.all(
        staffRows.map(async (staff) => {
          try {
            nextProfiles[staff.id] = await staffApi.faceProfile(staff.id);
          } catch {
            nextProfiles[staff.id] = null;
          }
        }),
      );
      setProfiles(nextProfiles);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Staff could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => () => {
    facePreviews.forEach(({ url }) => URL.revokeObjectURL(url));
  }, [facePreviews]);

  const filteredItems = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return items;
    return items.filter((item) =>
      [item.full_name, item.employee_code, item.email, item.department ?? "", item.designation ?? ""]
        .some((value) => value.toLowerCase().includes(term)),
    );
  }, [items, search]);

  function openCreate() {
    setMode("create");
    setActiveItem(null);
    setDraft({
      ...emptyDraft,
      joining_date: todayLocal(),
    });
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
    setFormOpen(true);
  }

  function openEdit(employee: Employee) {
    setMode("edit");
    setActiveItem(employee);
    setDraft(fromEmployee(employee));
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
    setFormOpen(true);
  }

  function closeModal() {
    setFormOpen(false);
    setActiveItem(null);
    setDraft(emptyDraft);
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
  }

  function clearFieldError(field: keyof FormErrors) {
    setFormErrors((current) => ({ ...current, [field]: undefined }));
    setFormError("");
  }

  function validateDraft() {
    const nextErrors: FormErrors = {};
    if (!draft.full_name.trim()) nextErrors.full_name = "Enter the employee's name.";
    if (!draft.email.trim()) nextErrors.email = "Enter a work email address.";
    else if (!/^\S+@\S+\.\S+$/.test(draft.email)) nextErrors.email = "Enter a valid email address.";
    if (mode === "create" && faceFiles.length < 3) nextErrors.faceFiles = "Add at least 3 clear face photos so recognition can work.";
    if (faceFiles.length > 10) nextErrors.faceFiles = "Use no more than 10 face photos.";
    setFormErrors(nextErrors);
    setFormError(Object.keys(nextErrors).length ? "Please fix the highlighted fields below." : "");
    return Object.keys(nextErrors).length === 0;
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validateDraft()) return;

    setSaving(true);
    setFormError("");

    let savedEmployee: Employee | null = null;
    try {
      const payload = toPayload(draft);
      savedEmployee = mode === "create"
        ? await staffApi.create(payload)
        : activeItem
          ? await staffApi.update(activeItem.id, payload)
          : null;
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : "Staff could not be saved.";
      if (message.toLowerCase().includes("email")) setFormErrors((current) => ({ ...current, email: message }));
      setFormError(message);
      setSaving(false);
      return;
    }

    if (!savedEmployee) {
      setSaving(false);
      return;
    }

    setItems((current) => {
      if (mode === "create") return [savedEmployee, ...current];
      return current.map((row) => (row.id === savedEmployee.id ? savedEmployee : row));
    });
    setProfiles((current) => ({
      ...current,
      [savedEmployee.id]: current[savedEmployee.id] ?? null,
    }));

    if (faceFiles.length > 0) {
      try {
        const enrollment = await staffApi.enrollFaces(savedEmployee.id, {
          files: faceFiles,
          re_enroll: mode === "edit",
        });
        setProfiles((current) => ({
          ...current,
          [savedEmployee.id]: enrollment.profile,
        }));
      } catch (caught) {
        const message = caught instanceof Error ? caught.message : "Face photos could not be enrolled.";
        setFormErrors({ faceFiles: message });
        setFormError(`${savedEmployee.full_name} was saved, but the face photos need attention.`);
        setActiveItem(savedEmployee);
        setDraft(fromEmployee(savedEmployee));
        setMode("edit");
        setSaving(false);
        await load();
        return;
      }
    }

    setToast({
      tone: "success",
      title: mode === "create" ? "Staff created" : "Staff updated",
      message: faceFiles.length > 0
        ? `${savedEmployee.full_name} was saved and face enrollment was updated.`
        : "Staff profile was saved successfully.",
    });
    closeModal();
    setSaving(false);
    await load();
  }

  async function toggleActive(employee: Employee) {
    try {
      setSaving(true);
      const updated = employee.is_active ? await staffApi.deactivate(employee.id) : await staffApi.activate(employee.id);
      setItems((current) => current.map((row) => (row.id === employee.id ? updated : row)));
      setToast({
        tone: "success",
        title: employee.is_active ? "Staff deactivated" : "Staff activated",
        message: `${employee.full_name} was updated.`,
      });
    } catch (caught) {
      setToast({
        tone: "error",
        title: "Update failed",
        message: caught instanceof Error ? caught.message : "Unable to change staff status.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function remove(employee: Employee) {
    if (!window.confirm(`Delete ${employee.full_name}? This removes the staff record and face enrollment.`)) return;
    try {
      setSaving(true);
      await staffApi.remove(employee.id);
      setItems((current) => current.filter((row) => row.id !== employee.id));
      setProfiles((current) => {
        const next = { ...current };
        delete next[employee.id];
        return next;
      });
      setToast({
        tone: "success",
        title: "Staff deleted",
        message: `${employee.full_name} was removed.`,
      });
    } catch (caught) {
      setToast({
        tone: "error",
        title: "Delete failed",
        message: caught instanceof Error ? caught.message : "Unable to delete staff.",
      });
    } finally {
      setSaving(false);
    }
  }

  const totalStaff = items.length;
  const activeStaff = items.filter((item) => item.is_active).length;
  const enrolledStaff = Object.values(profiles).filter((profile) => profile?.enrollment_status === "Enrolled").length;

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Common</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Staff</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Known office/company people used by camera recognition and future modules. This page stays available even when Attendance is disabled.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>
              Add Staff
            </Button>
            <Button
              variant="secondary"
              leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />}
              onClick={() => void load()}
              disabled={loading}
            >
              Refresh
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Total Staff</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : totalStaff}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Active Staff</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : activeStaff}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Face Enrolled</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : enrolledStaff}</div>
        </Card>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600">{error}</div> : null}

      <section className="grid gap-4 rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-slate-950/75 lg:grid-cols-[1fr_auto] lg:items-end">
        <Input
          label="Search staff"
          placeholder="Name, ID, email, department"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          leftIcon={<ScanFace className="h-4 w-4" />}
        />
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
          Employee IDs are generated automatically when you save.
        </div>
      </section>

      {loading ? (
        <Card className="h-40 animate-pulse bg-slate-100 dark:bg-white/5" />
      ) : filteredItems.length === 0 ? (
        <EmptyState
          title="No staff yet"
          description="Add the first staff record and upload face photos so the camera can recognize them."
          action={<Button onClick={openCreate}>Add Staff</Button>}
        />
      ) : (
        <DataTable
          title="Staff list"
          subtitle="Name, Employee ID, department, recognition status, and actions"
          headers={["Staff", "Department", "Designation", "Face", "Status", "Created", "Actions"]}
        >
          {filteredItems.map((item) => {
            const profile = profiles[item.id];
            const faceStatus = faceLabel(profile);
            return (
              <tr key={item.id}>
                <td className="px-5 py-4">
                  <div className="font-medium text-slate-900 dark:text-white">{item.full_name}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{item.employee_code}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{item.email}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{item.mobile ?? "-"}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{item.department ?? "-"}</td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{item.designation ?? "-"}</td>
                <td className="px-5 py-4">
                  <Badge tone={faceTone(faceStatus)}>{faceStatus}</Badge>
                </td>
                <td className="px-5 py-4">
                  <Badge tone={item.is_active ? "success" : "neutral"}>{item.is_active ? "Active" : "Inactive"}</Badge>
                </td>
                <td className="px-5 py-4 text-sm text-slate-500">{formatDate(item.created_at)}</td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" size="sm" leftIcon={<ImagePlus className="h-4 w-4" />} onClick={() => openEdit(item)}>
                      Add Photos
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(item)}>
                      Edit
                    </Button>
                    <Button
                      variant="secondary"
                      size="sm"
                      leftIcon={item.is_active ? <PowerOff className="h-4 w-4" /> : <Power className="h-4 w-4" />}
                      onClick={() => void toggleActive(item)}
                      disabled={saving}
                    >
                      {item.is_active ? "Inactive" : "Activate"}
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void remove(item)} disabled={saving}>
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </DataTable>
      )}

      <Modal
        open={formOpen}
        title={mode === "create" ? "Add staff" : "Edit staff"}
        description="Create a common staff record and upload clear face photos for recognition."
        onClose={closeModal}
        className="max-w-4xl"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={closeModal}>
              Cancel
            </Button>
            <Button
              type="submit"
              form="staff-form"
              leftIcon={saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
              disabled={saving}
            >
              {saving ? "Saving..." : mode === "create" ? "Create staff" : "Save staff"}
            </Button>
          </div>
        }
      >
        <form id="staff-form" onSubmit={save} className="grid gap-5" noValidate>
          {formError ? (
            <div role="alert" className="rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm font-medium text-rose-300">
              {formError}
            </div>
          ) : null}

          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/5 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Employee ID</p>
            <p className="mt-1 text-sm text-slate-300">
              {mode === "create" ? "Generated automatically when you save the staff profile." : activeItem?.employee_code ?? draft.employee_code}
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Employee Name *"
              autoFocus
              placeholder="e.g. Sakshi Sharma"
              value={draft.full_name}
              error={formErrors.full_name}
              onChange={(event) => {
                setDraft((current) => ({ ...current, full_name: event.target.value }));
                clearFieldError("full_name");
              }}
            />
            <Input
              label="Work Email *"
              type="email"
              placeholder="name@company.com"
              value={draft.email}
              error={formErrors.email}
              onChange={(event) => {
                setDraft((current) => ({ ...current, email: event.target.value }));
                clearFieldError("email");
              }}
            />
            <Input
              label="Phone"
              value={draft.mobile}
              onChange={(event) => setDraft((current) => ({ ...current, mobile: event.target.value }))}
            />
            <Input
              label="Department"
              value={draft.department}
              onChange={(event) => setDraft((current) => ({ ...current, department: event.target.value }))}
            />
            <Input
              label="Designation"
              value={draft.designation}
              onChange={(event) => setDraft((current) => ({ ...current, designation: event.target.value }))}
            />
            <Input
              label="Joining Date"
              type="date"
              value={draft.joining_date}
              onChange={(event) => setDraft((current) => ({ ...current, joining_date: event.target.value }))}
            />
          </div>

          <label className="flex items-center gap-3 rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-200">
            <input
              type="checkbox"
              checked={draft.is_active}
              onChange={(event) => setDraft((current) => ({ ...current, is_active: event.target.checked }))}
            />
            Active staff
          </label>

          <div className={`overflow-hidden rounded-3xl border border-dashed p-5 transition ${formErrors.faceFiles ? "border-rose-400/70 bg-rose-500/5" : "border-cyan-400/40 bg-gradient-to-br from-cyan-500/10 via-slate-950/20 to-blue-500/10"}`}>
            <label className="grid cursor-pointer place-items-center gap-3 rounded-2xl px-4 py-6 text-center transition hover:bg-white/5">
              <span className="grid h-14 w-14 place-items-center rounded-2xl bg-cyan-400/15 text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,0.12)]">
                <ImagePlus className="h-7 w-7" />
              </span>
              <span>
                <span className="block text-base font-semibold text-white">Add face photos {mode === "create" ? "*" : "(optional)"}</span>
                <span className="mt-1 block text-sm text-slate-400">Upload clear front-face photos so camera recognition can match this staff member.</span>
              </span>
              <span className="inline-flex items-center gap-2 rounded-xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-2 text-sm font-medium text-cyan-200">
                <Upload className="h-4 w-4" /> Choose photos
              </span>
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                multiple
                className="sr-only"
                onChange={(event) => {
                  const selected = Array.from(event.target.files ?? []).filter((file) => file.type.startsWith("image/")).slice(0, 10);
                  setFaceFiles(selected);
                  setFormErrors((current) => ({
                    ...current,
                    faceFiles: selected.length > 0 && selected.length < 3 && mode === "create" ? "Select at least 3 photos for recognition." : undefined,
                  }));
                  setFormError("");
                  event.currentTarget.value = "";
                }}
              />
            </label>

            {facePreviews.length > 0 ? (
              <div className="mt-4 grid grid-cols-3 gap-3 sm:grid-cols-5">
                {facePreviews.map(({ file, url }, index) => (
                  <div key={`${file.name}-${file.lastModified}`} className="group relative aspect-square overflow-hidden rounded-2xl border border-white/10 bg-slate-900">
                    <img src={url} alt={`Face preview ${index + 1}`} className="h-full w-full object-cover" />
                    <button
                      type="button"
                      aria-label={`Remove ${file.name}`}
                      onClick={() => setFaceFiles((current) => current.filter((_, itemIndex) => itemIndex !== index))}
                      className="absolute right-1.5 top-1.5 rounded-full bg-slate-950/85 p-1.5 text-white opacity-90 transition hover:bg-rose-500"
                    >
                      <X className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
              <span>Well-lit front-facing photos work best for recognition.</span>
              <span className={faceFiles.length >= 3 ? "font-semibold text-emerald-400" : ""}>{faceFiles.length}/10 selected</span>
            </div>
            {formErrors.faceFiles ? <p className="mt-2 text-sm font-medium text-rose-400">{formErrors.faceFiles}</p> : null}
          </div>
        </form>
      </Modal>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        </div>
      ) : null}
    </div>
  );
}

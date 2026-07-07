import { Loader2, Plus, RefreshCw, Save, ScanFace, Trash2, Pencil, Eye, Power, PowerOff, Upload, ImagePlus, X } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { Navigate, useNavigate, useSearchParams } from "react-router-dom";

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
import {
  activateEmployee,
  createEmployee,
  deactivateEmployee,
  deleteEmployee,
  fetchEmployeeFaceProfile,
  fetchEmployees,
  fetchFaceEnrollmentSummary,
  fetchShifts,
  updateEmployee,
  uploadFaceImages,
  type AttendanceShift,
  type Employee,
  type EmployeePayload,
} from "@/services/clientAdminAttendance";

const employeeTypes = ["Full Time", "Part Time", "Contract", "Intern"];
const faceStatuses = ["Not Enrolled", "Processing", "Enrolled", "Failed"];

type Draft = {
  employee_code: string;
  full_name: string;
  email: string;
  mobile: string;
  gender: string;
  date_of_birth: string;
  department: string;
  designation: string;
  shift_id: string;
  joining_date: string;
  employee_type: string;
  is_active: boolean;
};

type FaceProfileMap = Record<string, { status: string; face_count: number; embedding_count: number }>;

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
  gender: "",
  date_of_birth: "",
  department: "",
  designation: "",
  shift_id: "",
  joining_date: "",
  employee_type: "Full Time",
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
    gender: draft.gender.trim() || null,
    date_of_birth: draft.date_of_birth || null,
    department: draft.department.trim() || null,
    designation: draft.designation.trim() || null,
    shift_id: draft.shift_id || null,
    joining_date: draft.joining_date || null,
    employee_type: draft.employee_type,
    is_active: draft.is_active,
  };
}

function fromEmployee(employee: Employee): Draft {
  return {
    employee_code: employee.employee_code,
    full_name: employee.full_name,
    email: employee.email,
    mobile: employee.mobile ?? "",
    gender: employee.gender ?? "",
    date_of_birth: employee.date_of_birth ?? "",
    department: employee.department ?? "",
    designation: employee.designation ?? "",
    shift_id: employee.shift_id ?? "",
    joining_date: employee.joining_date ?? "",
    employee_type: employee.employee_type ?? "Full Time",
    is_active: employee.is_active,
  };
}

function faceTone(status: string) {
  if (status === "Enrolled") return "success" as const;
  if (status === "Processing") return "warning" as const;
  if (status === "Failed") return "danger" as const;
  return "neutral" as const;
}

export function EmployeeListPage() {
  const { currentTenant, user } = useApp();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [profiles, setProfiles] = useState<FaceProfileMap>({});
  const [summary, setSummary] = useState<{ total_employees: number; enrolled_employees: number; in_progress_employees: number; failed_employees: number; total_images: number; total_embeddings: number } | null>(null);
  const [shifts, setShifts] = useState<AttendanceShift[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<ToastState>(null);
  const [mode, setMode] = useState<"create" | "edit" | null>(null);
  const [activeEmployee, setActiveEmployee] = useState<Employee | null>(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [filters, setFilters] = useState({ search: "", department: "", shiftId: "", faceStatus: "" });
  const [faceFiles, setFaceFiles] = useState<File[]>([]);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [formError, setFormError] = useState("");
  const facePreviews = useMemo(
    () => faceFiles.map((file) => ({ file, url: URL.createObjectURL(file) })),
    [faceFiles],
  );

  usePageTitle("Vision Pass | Employees");

  const adminBasePath = user?.role === "CLIENT_ADMIN" ? "/client-admin" : "/tenant-admin";

  async function loadData(showRefreshing = false) {
    try {
      if (showRefreshing) setRefreshing(true);
      else setLoading(true);
      setError("");
      const [employeeRows, shiftRows, summaryRows] = await Promise.all([
        fetchEmployees({
          search: filters.search || undefined,
          department: filters.department || undefined,
          shiftId: filters.shiftId || undefined,
          faceStatus: filters.faceStatus || undefined,
        }),
        fetchShifts(),
        fetchFaceEnrollmentSummary(),
      ]);
      setEmployees(employeeRows);
      setShifts(shiftRows);
      setSummary(summaryRows);
      const nextProfiles: FaceProfileMap = {};
      await Promise.all(
        employeeRows.map(async (employee) => {
          try {
            const profile = await fetchEmployeeFaceProfile(employee.id);
            nextProfiles[employee.id] = {
              status: profile.enrollment_status,
              face_count: profile.face_count,
              embedding_count: profile.embedding_count,
            };
          } catch {
            nextProfiles[employee.id] = { status: "Not Enrolled", face_count: 0, embedding_count: 0 };
          }
        }),
      );
      setProfiles(nextProfiles);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to load employees.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const employeeId = searchParams.get("edit");
    if (!employeeId) return;
    const employee = employees.find((row) => row.id === employeeId);
    if (employee) {
      setMode("edit");
      setActiveEmployee(employee);
      setDraft(fromEmployee(employee));
      setSearchParams((current) => {
        current.delete("edit");
        return current;
      });
    }
  }, [employees, searchParams, setSearchParams]);

  const departments = useMemo(() => Array.from(new Set(employees.map((employee) => employee.department).filter(Boolean) as string[])), [employees]);

  useEffect(() => () => {
    facePreviews.forEach(({ url }) => URL.revokeObjectURL(url));
  }, [facePreviews]);

  function clearFieldError(field: keyof FormErrors) {
    setFormErrors((current) => ({ ...current, [field]: undefined }));
    setFormError("");
  }

  function openCreate() {
    const defaultShift = shifts.find((shift) => shift.is_default && shift.is_active) ?? shifts.find((shift) => shift.is_active);
    setMode("create");
    setActiveEmployee(null);
    setDraft({
      ...emptyDraft,
      department: "General",
      joining_date: todayLocal(),
      shift_id: defaultShift?.id ?? "",
    });
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
  }

  function openEdit(employee: Employee) {
    setMode("edit");
    setActiveEmployee(employee);
    setDraft(fromEmployee(employee));
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
  }

  function closeModal() {
    setMode(null);
    setActiveEmployee(null);
    setDraft(emptyDraft);
    setFaceFiles([]);
    setFormErrors({});
    setFormError("");
  }

  function validateDraft() {
    const nextErrors: FormErrors = {};
    if (!draft.full_name.trim()) nextErrors.full_name = "Enter the employee's name.";
    if (!draft.email.trim()) nextErrors.email = "Enter a work email address.";
    else if (!/^\S+@\S+\.\S+$/.test(draft.email)) nextErrors.email = "Enter a valid email address.";
    if (mode === "create" && faceFiles.length < 3) nextErrors.faceFiles = "Add at least 3 clear face photos.";
    if (faceFiles.length > 10) nextErrors.faceFiles = "Use no more than 10 face photos.";
    setFormErrors(nextErrors);
    setFormError(Object.keys(nextErrors).length ? "Please fix the highlighted fields below." : "");
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!validateDraft()) return;

    setSaving(true);
    setFormError("");
    const wasCreate = mode === "create";
    let savedEmployee: Employee | null = null;

    try {
      const payload = toPayload(draft);
      savedEmployee = wasCreate
        ? await createEmployee(payload)
        : activeEmployee
          ? await updateEmployee(activeEmployee.id, payload)
          : null;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to save employee.";
      if (message.toLowerCase().includes("email")) setFormErrors((current) => ({ ...current, email: message }));
      setFormError(message);
      setSaving(false);
      return;
    }

    if (!savedEmployee) {
      setSaving(false);
      return;
    }

    setEmployees((current) => wasCreate
      ? [savedEmployee as Employee, ...current.filter((row) => row.id !== savedEmployee?.id)]
      : current.map((row) => (row.id === savedEmployee?.id ? savedEmployee as Employee : row)));
    setProfiles((current) => ({
      ...current,
      [savedEmployee.id]: current[savedEmployee.id] ?? { status: "Not Enrolled", face_count: 0, embedding_count: 0 },
    }));
    if (wasCreate) {
      setSummary((current) => current ? { ...current, total_employees: current.total_employees + 1 } : current);
    }
    window.dispatchEvent(new CustomEvent("visionpass:employees-changed"));

    if (faceFiles.length > 0) {
      try {
        const enrollment = await uploadFaceImages(savedEmployee.id, {
          files: faceFiles,
          re_enroll: !wasCreate,
        });
        setProfiles((current) => ({
          ...current,
          [savedEmployee!.id]: {
            status: enrollment.profile.enrollment_status,
            face_count: enrollment.profile.face_count,
            embedding_count: enrollment.profile.embedding_count,
          },
        }));
        if (enrollment.profile.enrollment_status !== "Enrolled") {
          const rejected = enrollment.validation_results.find((result) => result.enrollment_status !== "valid");
          throw new Error(rejected?.message ?? "At least 3 photos must pass face-quality checks.");
        }
      } catch (err) {
        setMode("edit");
        setActiveEmployee(savedEmployee);
        setDraft(fromEmployee(savedEmployee));
        const message = err instanceof Error ? err.message : "The face photos could not be enrolled.";
        setFormErrors({ faceFiles: message });
        setFormError(`${wasCreate ? `Employee ${savedEmployee.employee_code} was created, but` : "Profile changes were saved, but"} the face photos need attention.`);
        setSaving(false);
        void loadData(true);
        return;
      }
    }

    setToast({
      tone: "success",
      title: wasCreate ? "Employee ready" : "Employee updated",
      message: faceFiles.length > 0
        ? `${savedEmployee.full_name} was saved and face enrollment completed.`
        : "Employee profile was saved successfully.",
    });
    closeModal();
    setSaving(false);
    await loadData(true);
  }

  async function handleActivate(employee: Employee) {
    try {
      setSaving(true);
      const updated = employee.is_active ? await deactivateEmployee(employee.id) : await activateEmployee(employee.id);
      setEmployees((current) => current.map((row) => (row.id === employee.id ? updated : row)));
      setToast({ tone: "success", title: employee.is_active ? "Employee deactivated" : "Employee activated", message: `${employee.full_name} was updated.` });
    } catch (err) {
      setToast({ tone: "error", title: "Update failed", message: err instanceof Error ? err.message : "Unable to change employee status." });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(employee: Employee) {
    if (!window.confirm(`Delete ${employee.full_name}? This removes the employee record.`)) return;
    try {
      setSaving(true);
      await deleteEmployee(employee.id);
      await loadData(true);
      setToast({ tone: "success", title: "Employee deleted", message: `${employee.full_name} was removed.` });
    } catch (err) {
      setToast({ tone: "error", title: "Delete failed", message: err instanceof Error ? err.message : "Unable to delete employee." });
    } finally {
      setSaving(false);
    }
  }

  const faceSummaryCards = [
    { label: "Total Employees", value: summary?.total_employees ?? employees.length },
    { label: "Enrolled", value: summary?.enrolled_employees ?? 0 },
    { label: "Processing", value: summary?.in_progress_employees ?? 0 },
    { label: "Failed", value: summary?.failed_employees ?? 0 },
  ];

  if (!currentTenant) return <Navigate to={`${adminBasePath}/dashboard`} replace />;

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Employee management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Employees for {currentTenant.name}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Manage tenant employees and move them into face enrollment without exposing any technical model controls.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadData(true)} disabled={refreshing || saving}>
              {refreshing ? "Refreshing..." : "Refresh"}
            </Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate} disabled={saving}>
              Add employee
            </Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {faceSummaryCards.map((card) => (
          <Card key={card.label} className="p-4">
            <div className="text-sm text-slate-500 dark:text-slate-400">{card.label}</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : card.value}</div>
          </Card>
        ))}
      </section>

      <Card className="grid gap-4 p-4">
        <div className="grid gap-4 md:grid-cols-4">
          <Input label="Search" value={filters.search} onChange={(event) => setFilters((current) => ({ ...current, search: event.target.value }))} />
          <Input label="Department" list="employee-departments" value={filters.department} onChange={(event) => setFilters((current) => ({ ...current, department: event.target.value }))} />
          <div>
            <div className="mb-1 text-sm font-medium text-slate-700 dark:text-slate-200">Shift</div>
            <select className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-slate-950/60 dark:text-white" value={filters.shiftId} onChange={(event) => setFilters((current) => ({ ...current, shiftId: event.target.value }))}>
              <option value="">All shifts</option>
              {shifts.map((shift) => (
                <option key={shift.id} value={shift.id}>
                  {shift.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <div className="mb-1 text-sm font-medium text-slate-700 dark:text-slate-200">Face status</div>
            <select className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-slate-950/60 dark:text-white" value={filters.faceStatus} onChange={(event) => setFilters((current) => ({ ...current, faceStatus: event.target.value }))}>
              <option value="">All statuses</option>
              {faceStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </div>
        </div>
        <datalist id="employee-departments">
          {departments.map((department) => (
            <option key={department} value={department} />
          ))}
        </datalist>
        <div className="flex justify-end">
          <Button variant="secondary" onClick={() => void loadData(true)} disabled={saving}>
            Apply filters
          </Button>
        </div>
      </Card>

      <DataTable
        title="Employee list"
        subtitle="Code, name, department, shift, face status, and actions"
        headers={["Employee", "Department", "Designation", "Shift", "Face Status", "Status", "Actions"]}
        emptyState={!loading && employees.length === 0 ? <EmptyState title="No employees yet" description="Create the first employee for this tenant to start face enrollment." action={<Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>Add employee</Button>} /> : null}
      >
        {loading ? (
          <tr>
            <td className="px-5 py-6 text-sm text-slate-500 dark:text-slate-400" colSpan={7}>
              Loading employees...
            </td>
          </tr>
        ) : (
          employees.map((employee) => {
            const profile = profiles[employee.id];
            const faceStatus = profile?.status ?? "Not Enrolled";
            const shift = shifts.find((item) => item.id === employee.shift_id);
            return (
              <tr key={employee.id}>
                <td className="px-5 py-4">
                  <div className="font-medium text-slate-900 dark:text-white">{employee.full_name}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{employee.employee_code}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{employee.email}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{employee.department ?? "-"}</td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{employee.designation ?? "-"}</td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{shift?.name ?? employee.shift_id ?? "-"}</td>
                <td className="px-5 py-4">
                  <Badge tone={faceTone(faceStatus)}>{faceStatus}</Badge>
                </td>
                <td className="px-5 py-4">
                  <Badge tone={employee.is_active ? "success" : "neutral"}>{employee.is_active ? "Active" : "Inactive"}</Badge>
                </td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    <Button variant="secondary" size="sm" leftIcon={<Eye className="h-4 w-4" />} onClick={() => navigate(`${adminBasePath}/attendance/employees/${employee.id}`)}>
                      View
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(employee)}>
                      Edit
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={<ScanFace className="h-4 w-4" />} onClick={() => navigate(`${adminBasePath}/attendance/face-enrollment?employeeId=${employee.id}`)}>
                      Enroll Face
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={employee.is_active ? <PowerOff className="h-4 w-4" /> : <Power className="h-4 w-4" />} onClick={() => void handleActivate(employee)} disabled={saving}>
                      {employee.is_active ? "Deactivate" : "Activate"}
                    </Button>
                    <Button variant="secondary" size="sm" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void handleDelete(employee)} disabled={saving}>
                      Delete
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })
        )}
      </DataTable>

      <Modal
        open={mode !== null}
        title={mode === "create" ? "Add employee" : "Edit employee"}
        description={mode === "create" ? "Name, email, and clear face photosâ€”that is all you need to get started." : "Update the employee profile or replace face photos."}
        onClose={closeModal}
        className="max-w-3xl"
        footer={
          <div className="flex flex-wrap items-center justify-between gap-3">
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {mode === "create" ? "Employee ID and sensible defaults are added automatically." : `Employee ID: ${draft.employee_code}`}
            </p>
            <div className="flex gap-2">
              <Button variant="secondary" onClick={closeModal}>Cancel</Button>
              <Button type="submit" form="employee-form" leftIcon={saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} disabled={saving}>
                {saving ? "Saving..." : mode === "create" ? "Create & enroll" : "Save employee"}
              </Button>
            </div>
          </div>
        }
      >
        <form id="employee-form" onSubmit={handleSubmit} className="grid gap-5" noValidate>
          {formError ? (
            <div role="alert" className="rounded-2xl border border-rose-400/40 bg-rose-500/10 px-4 py-3 text-sm font-medium text-rose-300">
              {formError}
            </div>
          ) : null}

          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/5 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-300">Employee ID</p>
            <p className="mt-1 text-sm text-slate-300">{mode === "create" ? "Generated automatically after you save" : draft.employee_code}</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Input
              label="Full name *"
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
              label="Work email *"
              type="email"
              placeholder="name@company.com"
              value={draft.email}
              error={formErrors.email}
              onChange={(event) => {
                setDraft((current) => ({ ...current, email: event.target.value }));
                clearFieldError("email");
              }}
            />
          </div>

          <div className={`overflow-hidden rounded-3xl border border-dashed p-5 transition ${formErrors.faceFiles ? "border-rose-400/70 bg-rose-500/5" : "border-cyan-400/40 bg-gradient-to-br from-cyan-500/10 via-slate-950/20 to-blue-500/10"}`}>
            <label className="grid cursor-pointer place-items-center gap-3 rounded-2xl px-4 py-6 text-center transition hover:bg-white/5">
              <span className="grid h-14 w-14 place-items-center rounded-2xl bg-cyan-400/15 text-cyan-300 shadow-[0_0_30px_rgba(34,211,238,0.12)]">
                <ImagePlus className="h-7 w-7" />
              </span>
              <span>
                <span className="block text-base font-semibold text-white">Add clear face photos {mode === "create" ? "*" : ""}</span>
                <span className="mt-1 block text-sm text-slate-400">Choose 3â€“10 images: front, slight left, and slight right.</span>
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
                  setFormErrors((current) => ({ ...current, faceFiles: selected.length > 0 && selected.length < 3 ? "Select at least 3 photos." : undefined }));
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
              <span>Well-lit photos without masks or sunglasses work best.</span>
              <span className={faceFiles.length >= 3 ? "font-semibold text-emerald-400" : ""}>{faceFiles.length}/10 selected</span>
            </div>
            {formErrors.faceFiles ? <p className="mt-2 text-sm font-medium text-rose-400">{formErrors.faceFiles}</p> : null}
          </div>

          <details className="group rounded-2xl border border-white/10 bg-white/[0.03] p-4" open={mode === "edit"}>
            <summary className="cursor-pointer list-none font-medium text-slate-200">
              Optional employment details
              <span className="ml-2 text-xs font-normal text-slate-500">Department, shift, phone, and more</span>
            </summary>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <Input label="Mobile" value={draft.mobile} onChange={(event) => setDraft((current) => ({ ...current, mobile: event.target.value }))} />
              <Input label="Department" value={draft.department} onChange={(event) => setDraft((current) => ({ ...current, department: event.target.value }))} />
              <Input label="Designation" value={draft.designation} onChange={(event) => setDraft((current) => ({ ...current, designation: event.target.value }))} />
              <div>
                <div className="mb-2 text-sm font-medium text-slate-300">Assigned shift</div>
                <select className="h-11 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 text-sm text-white outline-none focus:border-cyan-400" value={draft.shift_id} onChange={(event) => setDraft((current) => ({ ...current, shift_id: event.target.value }))}>
                  <option value="">No shift</option>
                  {shifts.map((shift) => <option key={shift.id} value={shift.id}>{shift.name}</option>)}
                </select>
              </div>
              <Input label="Joining date" type="date" value={draft.joining_date} onChange={(event) => setDraft((current) => ({ ...current, joining_date: event.target.value }))} />
              <div>
                <div className="mb-2 text-sm font-medium text-slate-300">Employee type</div>
                <select className="h-11 w-full rounded-2xl border border-white/10 bg-slate-950/70 px-4 text-sm text-white outline-none focus:border-cyan-400" value={draft.employee_type} onChange={(event) => setDraft((current) => ({ ...current, employee_type: event.target.value }))}>
                  {employeeTypes.map((type) => <option key={type} value={type}>{type}</option>)}
                </select>
              </div>
              <Input label="Gender" value={draft.gender} onChange={(event) => setDraft((current) => ({ ...current, gender: event.target.value }))} />
              <Input label="Date of birth" type="date" value={draft.date_of_birth} onChange={(event) => setDraft((current) => ({ ...current, date_of_birth: event.target.value }))} />
              <label className="flex items-center gap-3 rounded-2xl border border-white/10 px-4 py-3 text-sm text-slate-200 md:col-span-2">
                <input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft((current) => ({ ...current, is_active: event.target.checked }))} />
                Active employee
              </label>
            </div>
          </details>
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

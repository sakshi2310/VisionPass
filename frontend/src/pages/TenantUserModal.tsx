import { FormEvent, useEffect, useMemo, useState } from "react";

import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import type { TenantUserRecord } from "@/services/tenantUsers";

export type TenantUserFormValues = {
  fullName: string;
  email: string;
  password: string;
  confirmPassword: string;
  phone: string;
  role: string;
  department: string;
  designation: string;
  employeeId: string;
  accessZones: string;
  isActive: boolean;
  faceEnrolled: boolean;
  notes: string;
};

type Mode = "create" | "edit" | "view";

type TenantUserModalProps = {
  open: boolean;
  mode: Mode;
  user: TenantUserRecord | null;
  saving?: boolean;
  onClose: () => void;
  onSubmit: (values: {
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
  }) => Promise<void> | void;
};

const roleOptions = [
  { value: "TENANT_USER", label: "tenant_user" },
  { value: "SECURITY_GUARD", label: "security_guard" },
  { value: "RECEPTIONIST", label: "receptionist" },
  { value: "ATTENDANCE_OPERATOR", label: "attendance_operator" },
  { value: "CAMERA_OPERATOR", label: "camera_operator" },
  { value: "MANAGER", label: "manager" },
];

function buildInitialValues(user: TenantUserRecord | null): TenantUserFormValues {
  return {
    fullName: user?.fullName ?? "",
    email: user?.email ?? "",
    password: "",
    confirmPassword: "",
    phone: user?.phone ?? "",
    role: user?.role ?? "TENANT_USER",
    department: user?.department ?? "",
    designation: user?.designation ?? "",
    employeeId: user?.employeeId ?? "",
    accessZones: user?.accessZones?.join(", ") ?? "",
    isActive: user?.isActive ?? true,
    faceEnrolled: user?.faceEnrolled ?? false,
    notes: user?.notes ?? "",
  };
}

export function TenantUserModal({ open, mode, user, saving = false, onClose, onSubmit }: TenantUserModalProps) {
  const [values, setValues] = useState<TenantUserFormValues>(() => buildInitialValues(user));
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setValues(buildInitialValues(user));
      setError("");
    }
  }, [open, user]);

  const isViewMode = mode === "view";
  const title = useMemo(() => {
    if (mode === "create") return "Add Tenant User";
    if (mode === "edit") return "Edit Tenant User";
    return "View Tenant User";
  }, [mode]);

  function parseZones(value: string) {
    return value
      .split(/[,\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (isViewMode) return;
    setError("");
    if (!values.fullName.trim()) {
      setError("Full name is required.");
      return;
    }
    if (!values.email.trim()) {
      setError("Email is required.");
      return;
    }
    if (mode === "create" && !values.password.trim()) {
      setError("Password is required.");
      return;
    }
    if (values.password.trim() && values.password !== values.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    await onSubmit({
      full_name: values.fullName.trim(),
      email: values.email.trim(),
      password: values.password.trim(),
      phone: values.phone.trim() || null,
      role: values.role,
      department: values.department.trim() || null,
      designation: values.designation.trim() || null,
      employee_id: values.employeeId.trim() || null,
      access_zones: parseZones(values.accessZones),
      is_active: values.isActive,
      face_enrolled: values.faceEnrolled,
      notes: values.notes.trim() || null,
    });
  }

  return (
    <Modal
      open={open}
      title={title}
      description="Manage tenant users without exposing tenant_id to the browser."
      onClose={onClose}
      footer={
        <div className="flex flex-wrap justify-end gap-3">
          <Button variant="secondary" onClick={onClose}>
            {isViewMode ? "Close" : "Cancel"}
          </Button>
          {!isViewMode ? (
            <Button type="submit" form="tenant-user-form" disabled={saving}>
              {saving ? "Saving..." : mode === "create" ? "Create user" : "Save changes"}
            </Button>
          ) : null}
        </div>
      }
    >
      <form id="tenant-user-form" onSubmit={handleSubmit} className="grid gap-4">
        <div className="grid gap-4 md:grid-cols-2">
          <Input label="Full name" value={values.fullName} onChange={(event) => setValues((current) => ({ ...current, fullName: event.target.value }))} disabled={isViewMode} />
          <Input label="Email" type="email" value={values.email} onChange={(event) => setValues((current) => ({ ...current, email: event.target.value }))} disabled={isViewMode} />
          <Input label="Password" type="password" value={values.password} onChange={(event) => setValues((current) => ({ ...current, password: event.target.value }))} disabled={isViewMode} helpText={mode === "edit" ? "Leave blank to keep the current password." : undefined} />
          <Input label="Confirm password" type="password" value={values.confirmPassword} onChange={(event) => setValues((current) => ({ ...current, confirmPassword: event.target.value }))} disabled={isViewMode} />
          <Input label="Phone" value={values.phone} onChange={(event) => setValues((current) => ({ ...current, phone: event.target.value }))} disabled={isViewMode} />
          <label className="grid gap-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">User role</span>
            <select value={values.role} onChange={(event) => setValues((current) => ({ ...current, role: event.target.value }))} disabled={isViewMode} className="h-11 rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100 disabled:opacity-60">
              {roleOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <Input label="Department" value={values.department} onChange={(event) => setValues((current) => ({ ...current, department: event.target.value }))} disabled={isViewMode} />
          <Input label="Designation" value={values.designation} onChange={(event) => setValues((current) => ({ ...current, designation: event.target.value }))} disabled={isViewMode} />
          <Input label="Employee ID" value={values.employeeId} onChange={(event) => setValues((current) => ({ ...current, employeeId: event.target.value }))} disabled={isViewMode} />
          <label className="grid gap-2 md:col-span-2">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Access zones</span>
            <textarea
              rows={3}
              value={values.accessZones}
              onChange={(event) => setValues((current) => ({ ...current, accessZones: event.target.value }))}
              disabled={isViewMode}
              placeholder="Main Gate, Emergency Exit, Lab Floor"
              className="w-full rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100 disabled:opacity-60"
            />
          </label>
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/40">
            <input type="checkbox" checked={values.isActive} onChange={(event) => setValues((current) => ({ ...current, isActive: event.target.checked }))} disabled={isViewMode} />
            <span className="text-sm text-slate-700 dark:text-slate-200">Active account</span>
          </label>
          <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 dark:border-white/10 dark:bg-slate-950/40">
            <input type="checkbox" checked={values.faceEnrolled} onChange={(event) => setValues((current) => ({ ...current, faceEnrolled: event.target.checked }))} disabled={isViewMode} />
            <span className="text-sm text-slate-700 dark:text-slate-200">Face enrolled</span>
          </label>
        </div>

        <label className="grid gap-2">
          <span className="text-sm font-medium text-slate-600 dark:text-slate-300">Notes</span>
          <textarea
            rows={4}
            value={values.notes}
            onChange={(event) => setValues((current) => ({ ...current, notes: event.target.value }))}
            disabled={isViewMode}
            className="w-full rounded-2xl border border-slate-200 bg-white/90 px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100 disabled:opacity-60"
          />
        </label>

        {error ? <p className="text-sm text-rose-500">{error}</p> : null}
      </form>
    </Modal>
  );
}
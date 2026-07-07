import { Loader2, ScanFace, ArrowLeft, Edit3, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useNavigate, useParams } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  deleteFaceEnrollment,
  fetchEmployeeDetails,
  fetchEmployeeFaceEmbeddings,
  fetchEmployeeFaceImages,
  fetchEmployeeFaceProfile,
  type Employee,
  type EmployeeFaceEmbedding,
  type EmployeeFaceImage,
  type EmployeeFaceProfile,
} from "@/services/clientAdminAttendance";

function formatDate(value?: string | null) {
  if (!value) return "-";
  return new Date(value).toLocaleString(undefined, { month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" });
}

function faceTone(status: string) {
  if (status === "Enrolled") return "success" as const;
  if (status === "Processing") return "warning" as const;
  if (status === "Failed") return "danger" as const;
  return "neutral" as const;
}

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

export function EmployeeDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useApp();
  const adminBasePath = user?.role === "CLIENT_ADMIN" ? "/client-admin" : "/tenant-admin";
  const [employee, setEmployee] = useState<Employee | null>(null);
  const [profile, setProfile] = useState<EmployeeFaceProfile | null>(null);
  const [images, setImages] = useState<EmployeeFaceImage[]>([]);
  const [embeddings, setEmbeddings] = useState<EmployeeFaceEmbedding[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle(employee ? `Vision Pass | ${employee.full_name}` : "Vision Pass | Employee Profile");

  useEffect(() => {
    let active = true;

    async function loadEmployee() {
      if (!id) return;
      try {
        setLoading(true);
        const [employeeRow, profileRow, imageRows, embeddingRows] = await Promise.all([
          fetchEmployeeDetails(id),
          fetchEmployeeFaceProfile(id),
          fetchEmployeeFaceImages(id),
          fetchEmployeeFaceEmbeddings(id),
        ]);
        if (!active) return;
        setEmployee(employeeRow);
        setProfile(profileRow);
        setImages(imageRows.images);
        setEmbeddings(embeddingRows.embeddings);
      } catch {
        if (!active) return;
        setToast({ tone: "error", title: "Load failed", message: "Unable to load employee profile." });
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadEmployee();

    return () => {
      active = false;
    };
  }, [id]);

  async function handleDeleteEnrollment() {
    if (!id) return;
    if (!window.confirm("Delete this employee face enrollment?")) return;
    try {
      setSaving(true);
      await deleteFaceEnrollment(id);
      const [profileRow, imageRows, embeddingRows] = await Promise.all([
        fetchEmployeeFaceProfile(id),
        fetchEmployeeFaceImages(id),
        fetchEmployeeFaceEmbeddings(id),
      ]);
      setProfile(profileRow);
      setImages(imageRows.images);
      setEmbeddings(embeddingRows.embeddings);
      setToast({ tone: "success", title: "Face enrollment removed", message: "Face data has been cleared for this employee." });
    } catch (error) {
      setToast({ tone: "error", title: "Delete failed", message: error instanceof Error ? error.message : "Unable to delete face enrollment." });
    } finally {
      setSaving(false);
    }
  }

  if (!id) {
    return <Navigate to={`${adminBasePath}/attendance/employees`} replace />;
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Employee profile</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">{employee?.full_name ?? "Employee"}</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">View employee details, face enrollment status, and enrollment artifacts in one place.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<ArrowLeft className="h-4 w-4" />} onClick={() => navigate(`${adminBasePath}/attendance/employees`)}>
              Back
            </Button>
            <Button variant="secondary" leftIcon={<Edit3 className="h-4 w-4" />} onClick={() => navigate(`${adminBasePath}/attendance/employees?edit=${id}`)}>
              Edit Employee
            </Button>
            <Button variant="secondary" leftIcon={<ScanFace className="h-4 w-4" />} onClick={() => navigate(`${adminBasePath}/attendance/face-enrollment?employeeId=${id}`)}>
              Enroll / Re-enroll Face
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Face Status</div>
          <div className="mt-2"><Badge tone={faceTone(profile?.enrollment_status ?? "Not Enrolled")}>{profile?.enrollment_status ?? "Not Enrolled"}</Badge></div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Face Images</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{profile?.face_count ?? 0}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Embeddings</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{profile?.embedding_count ?? 0}</div>
        </Card>
        <Card className="p-4">
          <div className="text-sm text-slate-500 dark:text-slate-400">Last Enrollment</div>
          <div className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">{formatDate(profile?.last_enrolled_at ?? null)}</div>
        </Card>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Employee details</h2>
          {loading ? (
            <div className="text-sm text-slate-500 dark:text-slate-400">Loading employee...</div>
          ) : employee ? (
            <div className="grid gap-3 md:grid-cols-2">
              {[
                ["Employee Code", employee.employee_code],
                ["Email", employee.email],
                ["Mobile", employee.mobile ?? "-"],
                ["Gender", employee.gender ?? "-"],
                ["Department", employee.department ?? "-"],
                ["Designation", employee.designation ?? "-"],
                ["Shift ID", employee.shift_id ?? "-"],
                ["Joining Date", employee.joining_date ?? "-"],
                ["Employee Type", employee.employee_type],
                ["Status", employee.is_active ? "Active" : "Inactive"],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{label}</div>
                  <div className="mt-2 font-medium text-slate-900 dark:text-white">{value}</div>
                </div>
              ))}
            </div>
          ) : null}
        </Card>

        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Face enrollment summary</h2>
          <div className="grid gap-3">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              <div className="text-sm text-slate-500 dark:text-slate-400">Average Quality Score</div>
              <div className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{profile?.average_quality_score ?? "-"}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              <div className="text-sm text-slate-500 dark:text-slate-400">Images Stored</div>
              <div className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{images.length}</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
              <div className="text-sm text-slate-500 dark:text-slate-400">Active Embeddings</div>
              <div className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">{embeddings.filter((embedding) => embedding.is_active).length}</div>
            </div>
            <Button variant="secondary" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void handleDeleteEnrollment()} disabled={saving}>
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Delete face enrollment"}
            </Button>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent face images</h2>
          <div className="grid gap-3">
            {images.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">No face images stored yet.</div>
            ) : (
              images.map((image) => (
                <div key={image.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{image.original_filename ?? image.id}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">{image.image_type ?? "Image"}</div>
                    </div>
                    <Badge tone={faceTone(image.validation_status === "Validated" ? "Enrolled" : image.validation_status)}>{image.validation_status}</Badge>
                  </div>
                  <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">Created {formatDate(image.created_at)}</div>
                  {image.validation_message ? <div className="mt-2 text-sm text-rose-300">{image.validation_message}</div> : null}
                </div>
              ))
            )}
          </div>
        </Card>

        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recent embeddings</h2>
          <div className="grid gap-3">
            {embeddings.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">No embeddings stored yet.</div>
            ) : (
              embeddings.map((embedding) => (
                <div key={embedding.id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="font-medium text-slate-900 dark:text-white">{embedding.embedding_model}</div>
                      <div className="mt-1 text-sm text-slate-500 dark:text-slate-400">Version: {embedding.version ?? "-"}</div>
                    </div>
                    <Badge tone={embedding.is_active ? "success" : "neutral"}>{embedding.is_active ? "Active" : "Inactive"}</Badge>
                  </div>
                  <div className="mt-3 text-xs text-slate-500 dark:text-slate-400">Created {formatDate(embedding.created_at)}</div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        </div>
      ) : null}
    </div>
  );
}

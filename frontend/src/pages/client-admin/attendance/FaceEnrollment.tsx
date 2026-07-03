import { Camera, Loader2, RefreshCw, ScanFace, Upload } from "lucide-react";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchEmployees,
  fetchFaceEnrollmentSummary,
  FaceEnrollmentApiError,
  reEnrollFace,
  uploadFaceImages,
  type Employee,
  type FaceEnrollmentPayload,
  type FaceImageValidationResult,
} from "@/services/clientAdminAttendance";

function faceTone(status: string) {
  if (status === "Validated" || status === "Enrolled") return "success" as const;
  if (status === "Processing") return "warning" as const;
  if (status === "Failed" || status === "Rejected") return "danger" as const;
  return "neutral" as const;
}

type DraftImage = {
  name: string;
  dataUrl: string;
  width: number;
  height: number;
  type: string;
  size: number;
  file: File;
  validation?: FaceImageValidationResult;
};

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

async function loadImageMeta(file: File): Promise<DraftImage> {
  const dataUrl = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("Unable to read image file."));
    reader.readAsDataURL(file);
  });

  const size = file.size;
  const type = file.type || "image/jpeg";
  const dimensions = await new Promise<{ width: number; height: number }>((resolve, reject) => {
    const image = new Image();
    image.onload = () => resolve({ width: image.naturalWidth, height: image.naturalHeight });
    image.onerror = () => reject(new Error("Unable to load image dimensions."));
    image.src = dataUrl;
  });

  return {
    name: file.name,
    dataUrl,
    width: dimensions.width,
    height: dimensions.height,
    type,
    size,
    file,
  };
}

export function FaceEnrollmentPage() {
  const { currentTenant } = useApp();
  const [searchParams, setSearchParams] = useSearchParams();
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [summary, setSummary] = useState<{ total_employees: number; enrolled_employees: number; in_progress_employees: number; failed_employees: number; total_images: number; total_embeddings: number } | null>(null);
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(searchParams.get("employeeId") ?? "");
  const [images, setImages] = useState<DraftImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);
  const [reEnroll, setReEnroll] = useState(false);
  const [lastResponse, setLastResponse] = useState<{ profile: string; embeddings: number; images: number } | null>(null);

  usePageTitle("Vision Pass | Face Enrollment");

  useEffect(() => {
    let active = true;

    async function loadPage() {
      try {
        setLoading(true);
        const [employeeRows, summaryRows] = await Promise.all([fetchEmployees(), fetchFaceEnrollmentSummary()]);
        if (!active) return;
        setEmployees(employeeRows);
        setSummary(summaryRows);
      } catch (error) {
        if (!active) return;
        setToast({ tone: "error", title: "Load failed", message: error instanceof Error ? error.message : "Unable to load face enrollment data." });
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadPage();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const employeeId = searchParams.get("employeeId");
    if (employeeId) setSelectedEmployeeId(employeeId);
  }, [searchParams]);

  const selectedEmployee = useMemo(() => employees.find((employee) => employee.id === selectedEmployeeId) ?? null, [employees, selectedEmployeeId]);

  async function handleFiles(event: ChangeEvent<HTMLInputElement>) {
    const fileList = Array.from(event.target.files ?? []);
    if (fileList.length === 0) return;
    try {
      setSaving(true);
      const nextImages = await Promise.all(fileList.map((file) => loadImageMeta(file)));
      setImages(nextImages);
      setToast({ tone: "success", title: "Images prepared", message: `${nextImages.length} image(s) ready for server validation.` });
    } catch (error) {
      setToast({ tone: "error", title: "File error", message: error instanceof Error ? error.message : "Unable to prepare images." });
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit() {
    if (!selectedEmployeeId) {
      setToast({ tone: "error", title: "Select an employee", message: "Choose an employee before uploading face images." });
      return;
    }
    if (images.length === 0) {
      setToast({ tone: "error", title: "Add images", message: "Upload at least one face image to continue." });
      return;
    }

    const payload: FaceEnrollmentPayload = {
      re_enroll: reEnroll,
      files: images.map((image) => image.file),
    };

    try {
      setSaving(true);
      const response = reEnroll ? await reEnrollFace(selectedEmployeeId, payload) : await uploadFaceImages(selectedEmployeeId, payload);
      setImages((current) => current.map((image) => ({
        ...image,
        validation: response.validation_results.find((result) => result.filename === image.name),
      })));
      setLastResponse({ profile: response.profile.enrollment_status, embeddings: response.embeddings.length, images: response.images.length });
      const failedCount = response.validation_results.filter((result) => result.status === "Failed").length;
      setToast(failedCount > 0
        ? { tone: "error", title: "Some images were rejected", message: `${response.embeddings.length} image(s) enrolled; ${failedCount} need attention.` }
        : { tone: "success", title: "Enrollment saved", message: `Employee face status updated to ${response.profile.enrollment_status}.` });
      const summaryRows = await fetchFaceEnrollmentSummary();
      setSummary(summaryRows);
    } catch (error) {
      if (error instanceof FaceEnrollmentApiError && error.validationResults.length > 0) {
        setImages((current) => current.map((image) => ({
          ...image,
          validation: error.validationResults.find((result) => result.filename === image.name),
        })));
      }
      setToast({ tone: "error", title: "Enrollment failed", message: error instanceof Error ? error.message : "Unable to save face enrollment." });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Face enrollment</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Register employee face images</h1>
                        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              Upload face images for {currentTenant?.name ?? "the current tenant"}. Model thresholds stay hidden in Super Admin settings.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => window.location.reload()} disabled={saving}>
              Refresh
            </Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Employees", value: summary?.total_employees ?? employees.length },
          { label: "Enrolled", value: summary?.enrolled_employees ?? 0 },
          { label: "Images", value: summary?.total_images ?? 0 },
          { label: "Embeddings", value: summary?.total_embeddings ?? 0 },
        ].map((card) => (
          <Card key={card.label} className="p-4">
            <div className="text-sm text-slate-500 dark:text-slate-400">{card.label}</div>
            <div className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : card.value}</div>
          </Card>
        ))}
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Enrollment wizard</h2>
          <div className="grid gap-4">
            <div>
              <div className="mb-1 text-sm font-medium text-slate-700 dark:text-slate-200">Employee</div>
              <select className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-cyan-400 dark:border-white/10 dark:bg-slate-950/60 dark:text-white" value={selectedEmployeeId} onChange={(event) => {
                setSelectedEmployeeId(event.target.value);
                setSearchParams(event.target.value ? { employeeId: event.target.value } : {});
              }}>
                <option value="">Select employee</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>
                    {employee.full_name} - {employee.employee_code}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex cursor-pointer flex-col gap-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
              <span className="flex items-center gap-2 font-medium text-slate-900 dark:text-white"><Upload className="h-4 w-4" /> Upload face images</span>
              <span>Choose 3 to 10 clear face images from the device.</span>
              <input type="file" accept="image/*" multiple className="hidden" onChange={(event) => void handleFiles(event)} disabled={saving} />
            </label>

            <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
              <input type="checkbox" checked={reEnroll} onChange={(event) => setReEnroll(event.target.checked)} />
              Re-enroll and deactivate prior embeddings
            </label>

            <Button leftIcon={saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanFace className="h-4 w-4" />} onClick={() => void handleSubmit()} disabled={saving || loading}>
              {saving ? "Validating..." : "Validate and enroll"}
            </Button>
          </div>
        </Card>

        <Card className="grid gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Enrollment status</h2>
          {images.length === 0 ? (
            <EmptyState title="No images prepared" description="Upload face photos to review them before saving." action={<Camera className="h-5 w-5 text-slate-400" />} />
          ) : (
            <div className="grid gap-3 md:grid-cols-2">
              {images.map((image) => (
                <div key={image.name} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                  <div className="aspect-[4/3] overflow-hidden rounded-2xl bg-slate-900/5 dark:bg-black/20">
                    <img src={image.dataUrl} alt={image.name} className="h-full w-full object-cover" />
                  </div>
                  <div className="mt-3 font-medium text-slate-900 dark:text-white">{image.name}</div>
                  <div className="mt-1 text-xs text-slate-500 dark:text-slate-400">{image.width} x {image.height} · {(image.size / 1024).toFixed(1)} KB</div>
                  <Badge tone={faceTone(image.validation?.status ?? "Pending")} className="mt-3">
                    {image.validation?.enrollment_status === "valid"
                      ? "Valid"
                      : image.validation?.enrollment_status === "rejected"
                        ? "Rejected"
                        : "Pending server validation"}
                  </Badge>
                  {image.validation ? (
                    <div className={`mt-3 rounded-xl p-3 text-xs leading-5 ${
                      image.validation.status === "Validated"
                        ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
                        : "bg-rose-500/10 text-rose-700 dark:text-rose-300"
                    }`}>
                      {image.validation.code ? <div className="font-semibold">{image.validation.code.replaceAll("_", " ")}</div> : null}
                      <div>{image.validation.message}</div>
                      {image.validation.detection_confidence != null ? (
                        <div className="mt-1">Detection confidence: {(image.validation.detection_confidence * 100).toFixed(1)}%</div>
                      ) : null}
                      {image.validation.quality_score != null ? (
                        <div>Quality score: {(image.validation.quality_score * 100).toFixed(1)}%</div>
                      ) : null}
                      {image.validation.duplicate_employee_name ? (
                        <div>Already enrolled as: {image.validation.duplicate_employee_name}</div>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card className="grid gap-4 p-5">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Selected employee</h2>
        {selectedEmployee ? (
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
            {[
              ["Name", selectedEmployee.full_name],
              ["Code", selectedEmployee.employee_code],
              ["Department", selectedEmployee.department ?? "-"],
              ["Status", selectedEmployee.is_active ? "Active" : "Inactive"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">
                <div className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{label}</div>
                <div className="mt-2 font-medium text-slate-900 dark:text-white">{value}</div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
            Select an employee to start enrollment.
          </div>
        )}
        {lastResponse ? (
          <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4 text-sm text-cyan-100">
            Last save: {lastResponse.profile} status with {lastResponse.images} images and {lastResponse.embeddings} embeddings.
          </div>
        ) : null}
      </Card>

      <Card className="grid gap-4 p-5">
        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Webcam capture</h2>
        <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-white/10 dark:bg-white/5 dark:text-slate-400">
          Webcam capture is reserved for the next pass. The upload path is wired now, and the service layer already accepts the same face payload shape for a future capture flow.
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



import { AlertTriangle, Camera, CheckCircle2, Clock3, Loader2, RefreshCw, ScanFace, Upload } from "lucide-react";
import { ChangeEvent, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  FaceEnrollmentApiError,
  fetchTodayAttendance,
  recognizeAndMarkAttendance,
  type RecognizeAndMarkResponse,
  type TodayAttendanceItem,
} from "@/services/clientAdminAttendance";

function statusTone(status: TodayAttendanceItem["status"]) {
  if (status === "present") return "success" as const;
  if (status === "late" || status === "half_day") return "warning" as const;
  if (status === "holiday") return "info" as const;
  return "neutral" as const;
}

function formatTime(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function formatDuration(minutes: number) {
  const hours = Math.floor(minutes / 60);
  const remainder = minutes % 60;
  return `${hours}h ${remainder}m`;
}

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

export function LiveAttendancePage() {
  const [records, setRecords] = useState<TodayAttendanceItem[]>([]);
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [lastResult, setLastResult] = useState<RecognizeAndMarkResponse | null>(null);
  const [warning, setWarning] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle("Vision Pass | Live Attendance");

  async function loadToday() {
    try {
      setLoading(true);
      setRecords(await fetchTodayAttendance());
    } catch (error) {
      setToast({
        tone: "error",
        title: "Attendance unavailable",
        message: error instanceof Error ? error.message : "Unable to load today's attendance.",
      });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadToday();
  }, []);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  function handleImage(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0] ?? null;
    setImage(next);
    setLastResult(null);
    setWarning("");
    setPreview(next ? URL.createObjectURL(next) : "");
  }

  async function handleRecognize() {
    if (!image) {
      setToast({ tone: "error", title: "Add a frame", message: "Choose a clear employee face image first." });
      return;
    }
    try {
      setProcessing(true);
      setWarning("");
      const result = await recognizeAndMarkAttendance(image);
      setLastResult(result);
      if (!result.recognition.recognized) {
        setWarning(`Face was not marked: ${result.recognition.recognition_status.replaceAll("_", " ").toLowerCase()}.`);
        return;
      }
      if (result.attendance) {
        setToast({
          tone: "success",
          title: result.attendance.event.event_type === "check_in" ? "Check-in complete" : "Check-out complete",
          message: `${result.attendance.employee_name}: ${result.attendance.message}`,
        });
        await loadToday();
      }
    } catch (error) {
      const code = error instanceof FaceEnrollmentApiError ? error.code : undefined;
      const message = error instanceof Error ? error.message : "Unable to process attendance.";
      if (code?.startsWith("DUPLICATE_") || code === "ALREADY_CHECKED_OUT" || code === "ALREADY_CHECKED_IN") {
        setWarning(message);
      }
      setToast({ tone: "error", title: "Attendance not marked", message });
    } finally {
      setProcessing(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Live attendance</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Recognize and mark attendance</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Submit a live camera frame or face image. Vision Pass determines check-in or check-out and applies duplicate protection automatically.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadToday()} disabled={loading || processing}>
            Refresh today
          </Button>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
        <Card className="grid gap-4 p-5">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recognition frame</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Exactly one clear face should be visible.</p>
          </div>

          <label className="flex cursor-pointer items-center gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-700 dark:border-white/10 dark:bg-white/5 dark:text-slate-200">
            <Upload className="h-5 w-5 text-cyan-500" />
            <span>{image?.name ?? "Choose an image or captured frame"}</span>
            <input type="file" accept="image/*" capture="user" className="hidden" onChange={handleImage} disabled={processing} />
          </label>

          <div className="grid aspect-video place-items-center overflow-hidden rounded-2xl bg-slate-950/90">
            {preview ? (
              <img src={preview} alt="Recognition frame" className="h-full w-full object-contain" />
            ) : (
              <Camera className="h-12 w-12 text-slate-600" />
            )}
          </div>

          <Button
            leftIcon={processing ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanFace className="h-4 w-4" />}
            onClick={() => void handleRecognize()}
            disabled={processing}
          >
            {processing ? "Recognizing..." : "Recognize and mark"}
          </Button>

          {warning ? (
            <div className="flex gap-3 rounded-2xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm text-amber-800 dark:text-amber-200">
              <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
              <div>
                <div className="font-semibold">Attendance warning</div>
                <div className="mt-1">{warning}</div>
              </div>
            </div>
          ) : null}
        </Card>

        <Card className="grid content-start gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Recognized employee</h2>
          {!lastResult ? (
            <EmptyState title="Waiting for recognition" description="The latest recognized employee and attendance status will appear here." action={<ScanFace className="h-6 w-6 text-slate-400" />} />
          ) : lastResult.recognition.recognized && lastResult.attendance ? (
            <div className="grid gap-4">
              <div className="flex items-center gap-4 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-5">
                <div className="grid h-12 w-12 place-items-center rounded-full bg-emerald-500/20">
                  <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                </div>
                <div>
                  <div className="text-xl font-semibold text-slate-900 dark:text-white">{lastResult.attendance.employee_name}</div>
                  <div className="text-sm text-slate-500 dark:text-slate-400">{lastResult.attendance.employee_code}</div>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                  <div className="text-xs uppercase tracking-wider text-slate-500">Action</div>
                  <div className="mt-2 font-semibold capitalize">{lastResult.attendance.event.event_type.replace("_", " ")}</div>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                  <div className="text-xs uppercase tracking-wider text-slate-500">Daily status</div>
                  <div className="mt-2 font-semibold capitalize">{lastResult.attendance.daily.status.replace("_", " ")}</div>
                </div>
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                  <div className="text-xs uppercase tracking-wider text-slate-500">Confidence</div>
                  <div className="mt-2 font-semibold">{((lastResult.recognition.confidence ?? 0) * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-5 dark:border-white/10 dark:bg-white/5">
              <Badge tone="warning">{lastResult.recognition.recognition_status.replaceAll("_", " ")}</Badge>
              <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">No attendance event was created.</p>
            </div>
          )}
        </Card>
      </div>

      <DataTable
        title="Today's attendance"
        subtitle={`${records.length} employee record(s) today`}
        headers={["Employee", "Status", "First check-in", "Last check-out", "Worked"]}
        emptyState={!loading && records.length === 0 ? <div className="p-6"><EmptyState title="No attendance yet" description="Recognized check-ins will appear here." action={<Clock3 className="h-5 w-5 text-slate-400" />} /></div> : undefined}
      >
        {records.map((record) => (
          <tr key={record.id}>
            <td className="px-5 py-4">
              <div className="font-medium text-slate-900 dark:text-white">{record.employee_name}</div>
              <div className="text-xs text-slate-500">{record.employee_code}</div>
            </td>
            <td className="px-5 py-4"><Badge tone={statusTone(record.status)}>{record.status.replace("_", " ")}</Badge></td>
            <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatTime(record.first_check_in)}</td>
            <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatTime(record.last_check_out)}</td>
            <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{formatDuration(record.total_work_minutes)}</td>
          </tr>
        ))}
      </DataTable>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} />
        </div>
      ) : null}
    </div>
  );
}

import { Camera, CheckCircle2, Clock3, Loader2, RefreshCw, ScanFace, ShieldCheck, UserX } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchCameras,
  fetchCameraSnapshot,
  processCameraFrame,
  recognizeAndMarkCameraAttendance,
  recognizeCameraFrame,
  type Camera as CameraRecord,
  type CameraFrameResult,
} from "@/services/clientAdminAttendance";

type Action = "capture" | "recognize" | "mark";

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

function formatTime(value?: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

function frameStatusTone(status?: string | null) {
  if (status === "online") return "success" as const;
  if (status === "unknown") return "neutral" as const;
  return "danger" as const;
}

export function LiveRecognitionPage() {
  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [cameraId, setCameraId] = useState("");
  const [result, setResult] = useState<CameraFrameResult | null>(null);
  const [preview, setPreview] = useState("");
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState<Action | null>(null);
  const [cooldown, setCooldown] = useState(0);
  const [toast, setToast] = useState<ToastState>(null);
  const autoBusyRef = useRef(false);

  usePageTitle("Vision Pass | Live Recognition");

  async function loadCameras() {
    try {
      setLoading(true);
      const rows = await fetchCameras();
      setCameras(rows);
      const firstAvailable = rows.find((camera) => camera.is_active && camera.snapshot_url);
      setCameraId((current) => current || firstAvailable?.id || "");
    } catch (error) {
      setToast({ tone: "error", title: "Cameras unavailable", message: error instanceof Error ? error.message : "Unable to load cameras." });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCameras();
  }, []);

  useEffect(() => {
    const interval = window.setInterval(() => {
      if (!action) {
        void loadCameras();
      }
    }, 15000);
    return () => window.clearInterval(interval);
  }, [action]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setInterval(() => setCooldown((value) => Math.max(0, value - 1)), 1000);
    return () => window.clearInterval(timer);
  }, [cooldown]);

  const selectedCamera = useMemo(
    () => cameras.find((camera) => camera.id === cameraId) ?? null,
    [cameraId, cameras],
  );

  useEffect(() => {
    if (!selectedCamera?.is_active || !selectedCamera.snapshot_url) return;

    const runRecognition = () => {
      if (document.visibilityState !== "visible") return;
      if (autoBusyRef.current) return;

      autoBusyRef.current = true;
      void (async () => {
        try {
          const response = await recognizeAndMarkCameraAttendance(cameraId);
          setResult(response);
          setCooldown(response.frame.frame_interval_seconds);
          await updatePreview(cameraId);
          await loadCameras();
        } catch (error) {
          setToast({
            tone: "error",
            title: "Auto recognition failed",
            message: error instanceof Error ? error.message : "Unable to process live camera frame.",
          });
        } finally {
          autoBusyRef.current = false;
        }
      })();
    };

    runRecognition();
    const timer = window.setInterval(runRecognition, 5000);

    return () => window.clearInterval(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cameraId, selectedCamera?.id, selectedCamera?.is_active, selectedCamera?.snapshot_url]);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);
    };
  }, [preview]);

  async function updatePreview(selectedId: string) {
    const blob = await fetchCameraSnapshot(selectedId);
    setPreview(URL.createObjectURL(blob));
  }

  async function runAction(nextAction: Action) {
    if (!cameraId) {
      setToast({ tone: "error", title: "Select a camera", message: "Choose an active snapshot camera first." });
      return;
    }
    try {
      setAction(nextAction);
      const response = nextAction === "capture"
        ? await processCameraFrame(cameraId)
        : nextAction === "recognize"
          ? await recognizeCameraFrame(cameraId)
          : await recognizeAndMarkCameraAttendance(cameraId);
      setResult(response);
      setCooldown(response.frame.frame_interval_seconds);
      await updatePreview(cameraId);
      await loadCameras();

      if (response.attendance) {
        setToast({
          tone: "success",
          title: response.attendance.event.event_type === "check_in" ? "Check-in recorded" : "Check-out recorded",
          message: `${response.attendance.employee_name}: ${response.attendance.message}`,
        });
      } else if (response.recognition?.recognized) {
        setToast({ tone: "success", title: "Employee recognized", message: response.recognition.employee_name ?? "Matched employee." });
      } else if (response.recognition?.recognition_status === "NO_FACE") {
        setToast({ tone: "error", title: "No face detected", message: "No employee attendance was changed." });
      } else if (response.recognition?.recognition_status === "UNKNOWN") {
        setToast({ tone: "error", title: "Unknown face detected", message: "No employee attendance was changed." });
      } else if (nextAction === "capture") {
        setToast({ tone: "success", title: "Frame captured", message: `${response.frame.width} × ${response.frame.height} image validated.` });
      }
    } catch (error) {
      setToast({ tone: "error", title: "Camera processing failed", message: error instanceof Error ? error.message : "Unable to process camera frame." });
      await loadCameras();
    } finally {
      setAction(null);
    }
  }

  const controlsDisabled = loading || action !== null || cooldown > 0 || !cameraId;
  const selectedCameraLabel = selectedCamera ? `${selectedCamera.name} · ${selectedCamera.location}` : "Select camera";

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Live recognition</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Process live camera frames</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Capture a validated frame, recognize an enrolled employee, or recognize and mark attendance in one step.</p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadCameras()} disabled={loading || action !== null}>
            Refresh cameras
          </Button>
        </div>
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="grid gap-4 p-5">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <label className="grid flex-1 gap-1 text-sm">
              Camera
              <select
                className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900"
                value={cameraId}
                onChange={(event) => {
                  setCameraId(event.target.value);
                  setResult(null);
                  setPreview("");
                }}
              >
                <option value="">Select camera</option>
                {cameras.filter((camera) => camera.is_active && camera.snapshot_url).map((camera) => (
                  <option key={camera.id} value={camera.id}>{camera.name} - {camera.location}</option>
                ))}
              </select>
            </label>
            {selectedCamera ? <Badge tone={frameStatusTone(selectedCamera.health_status)}>{selectedCamera.health_status}</Badge> : null}
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
              <div className="text-xs uppercase tracking-wider text-slate-500">Camera</div>
              <div className="mt-2 font-semibold text-slate-900 dark:text-white">{selectedCameraLabel}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
              <div className="text-xs uppercase tracking-wider text-slate-500">Enabled</div>
              <div className="mt-2 font-semibold text-slate-900 dark:text-white">{selectedCamera?.is_active ? "Enabled" : "Disabled"}</div>
            </div>
            <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
              <div className="text-xs uppercase tracking-wider text-slate-500">Last frame</div>
              <div className="mt-2 font-semibold text-slate-900 dark:text-white">{formatTime(selectedCamera?.last_seen_at)}</div>
            </div>
          </div>

          <div className="grid aspect-video place-items-center overflow-hidden rounded-3xl bg-slate-950">
            {preview ? <img src={preview} alt="Latest camera frame" className="h-full w-full object-contain" /> : <Camera className="h-14 w-14 text-slate-700" />}
          </div>

          <div className="grid gap-2 sm:grid-cols-3">
            <Button variant="secondary" leftIcon={action === "capture" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Camera className="h-4 w-4" />} onClick={() => void runAction("capture")} disabled={controlsDisabled}>Capture frame</Button>
            <Button variant="secondary" leftIcon={action === "recognize" ? <Loader2 className="h-4 w-4 animate-spin" /> : <ScanFace className="h-4 w-4" />} onClick={() => void runAction("recognize")} disabled={controlsDisabled}>Recognize</Button>
            <Button leftIcon={action === "mark" ? <Loader2 className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />} onClick={() => void runAction("mark")} disabled={controlsDisabled}>Recognize & mark</Button>
          </div>
          {cooldown > 0 ? <div className="flex items-center justify-center gap-2 text-xs text-slate-500"><Clock3 className="h-4 w-4" />Next frame available in {cooldown}s</div> : null}
        </Card>

        <Card className="grid content-start gap-4 p-5">
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Latest result</h2>
          {!result ? (
            <EmptyState title="No frame processed" description="Choose an action to see recognition and attendance results." action={<ScanFace className="h-6 w-6 text-slate-400" />} />
          ) : result.recognition?.recognized ? (
            <div className="grid gap-4">
              <div className="flex gap-3 rounded-2xl border border-emerald-400/20 bg-emerald-500/10 p-4">
                <CheckCircle2 className="h-6 w-6 text-emerald-500" />
                <div>
                  <div className="font-semibold text-slate-900 dark:text-white">{result.recognition.employee_name}</div>
                  <div className="text-sm text-emerald-700 dark:text-emerald-300">Matched at {((result.recognition.confidence ?? 0) * 100).toFixed(1)}%</div>
                </div>
              </div>
              {result.attendance ? (
                <div className="rounded-2xl bg-slate-50 p-4 dark:bg-white/5">
                  <div className="text-xs uppercase tracking-wider text-slate-500">Attendance</div>
                  <div className="mt-2 font-semibold capitalize">{result.attendance.event.event_type.replaceAll("_", " ")} · {result.attendance.daily.status.replaceAll("_", " ")}</div>
                  <div className="mt-1 text-sm text-slate-500">{result.attendance.message}</div>
                </div>
              ) : (
                <div className="rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4">
                  <div className="font-semibold text-slate-900 dark:text-white">Employee recognized, no attendance event created</div>
                  <div className="mt-1 text-sm text-slate-500">
                    {String(result.camera_event.metadata?.attendance_reason ?? "Already checked in today")}
                  </div>
                </div>
              )}
            </div>
          ) : result.recognition ? (
            <div className="flex gap-3 rounded-2xl border border-amber-400/20 bg-amber-500/10 p-4">
              <UserX className="h-6 w-6 text-amber-500" />
              <div>
                <div className="font-semibold">
                  {result.recognition.recognition_status === "NO_FACE"
                    ? "No face detected"
                    : result.recognition.recognition_status === "UNKNOWN"
                      ? "Unknown face detected"
                      : result.recognition.recognition_status.replaceAll("_", " ")}
                </div>
                <div className="mt-1 text-sm text-slate-500">No employee attendance was changed.</div>
              </div>
            </div>
          ) : (
            <div className="rounded-2xl border border-cyan-400/20 bg-cyan-500/10 p-4">
              <div className="font-semibold">Frame captured</div>
              <div className="mt-1 text-sm text-slate-500">{result.frame.width} × {result.frame.height} · {result.frame.content_type}</div>
            </div>
          )}
          {result ? (
            <div className="text-xs text-slate-500">
              Event: {result.camera_event.event_type} · {result.camera_event.recognition_status}
              {result.camera_event.metadata?.attendance_status ? ` · ${String(result.camera_event.metadata.attendance_status).replaceAll("_", " ")}` : ""}
            </div>
          ) : null}
        </Card>
      </div>

      {cameras.filter((camera) => camera.is_active && camera.snapshot_url).length === 0 && !loading ? (
        <Card className="p-5"><EmptyState title="No snapshot camera available" description="Configure an active IP Webcam snapshot URL in Camera Management first." action={<Camera className="h-6 w-6 text-slate-400" />} /></Card>
      ) : null}

      {toast ? <div className="fixed right-4 top-4 z-50"><Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} /></div> : null}
    </div>
  );
}

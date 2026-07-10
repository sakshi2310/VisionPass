import { ExternalLink, Plus, RefreshCw, Video } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { fetchCameras, recognizeAndMarkCameraAttendance, type Camera, type CameraFrameResult } from "@/services/clientAdminAttendance";

function feedUrl(camera: Camera, version: number) {
  const rawUrl = camera.snapshot_url ?? (camera.stream_url?.startsWith("http") ? camera.stream_url : "");
  if (!rawUrl) return "";
  return `${rawUrl}${rawUrl.includes("?") ? "&" : "?"}vpRefresh=${version}`;
}

function formatClockTime(value?: string) {
  if (!value) return "";
  return new Intl.DateTimeFormat(undefined, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export function CameraZoneViewPage() {
  const navigate = useNavigate();
  const { user, hasModule } = useApp();
  const basePath = user?.role === "TENANT_ADMIN" ? "/tenant-admin" : "/client-admin";
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [feedVersions, setFeedVersions] = useState<Record<string, number>>({});
  const [autoStatus, setAutoStatus] = useState<Record<string, { running: boolean; label: string; updated_at?: string }>>({});
  const autoBusyRef = useRef<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<{ tone: "success" | "error"; title: string; message: string } | null>(null);

  usePageTitle("Vision Pass | Zone View");

  const activeCameras = useMemo(() => cameras.filter((camera) => camera.is_active), [cameras]);

  async function loadCameras() {
    try {
      setLoading(true);
      const response = await fetchCameras();
      setCameras(response);
    } catch (error) {
      setMessage({ tone: "error", title: "Cameras unavailable", message: error instanceof Error ? error.message : "Unable to load cameras." });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCameras();
  }, []);

  useEffect(() => {
    if (!activeCameras.some((camera) => camera.snapshot_url)) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState !== "visible") return;
      setFeedVersions((current) => {
        const next = { ...current };
        activeCameras.forEach((camera) => {
          if (camera.snapshot_url) next[camera.id] = (current[camera.id] ?? 0) + 1;
        });
        return next;
      });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [activeCameras]);

  useEffect(() => {
    if (!hasModule("attendance")) return;

    const eligibleCameras = activeCameras.filter(
      (camera) => camera.snapshot_url && (camera.assigned_feature_scope === "attendance" || camera.assigned_feature_scope === "both"),
    );
    if (!eligibleCameras.length) return;

    const interval = window.setInterval(() => {
      if (document.visibilityState !== "visible") return;
      eligibleCameras.forEach((camera) => {
        if (autoBusyRef.current[camera.id]) return;
        autoBusyRef.current[camera.id] = true;
        setAutoStatus((current) => ({
          ...current,
          [camera.id]: { running: true, label: "Recognizing..." },
        }));

        void recognizeAndMarkCameraAttendance(camera.id)
          .then((result: CameraFrameResult) => {
            const recognized = result.recognition?.recognized ?? false;
            const statusLabel = result.attendance
              ? `Marked ${result.attendance.event.event_type.replaceAll("_", " ")}`
              : recognized
                ? `Recognized ${result.recognition?.employee_name ?? "employee"}`
                : result.recognition?.recognition_status === "NO_FACE"
                  ? "No face"
                  : result.recognition?.recognition_status === "UNKNOWN"
                    ? "Unknown face"
                    : "No update";

            setAutoStatus((current) => ({
              ...current,
              [camera.id]: {
                running: false,
                label: statusLabel,
                updated_at: new Date().toISOString(),
              },
            }));
          })
          .catch((error) => {
            setAutoStatus((current) => ({
              ...current,
              [camera.id]: {
                running: false,
                label: error instanceof Error ? error.message : "Recognition failed",
                updated_at: new Date().toISOString(),
              },
            }));
          })
          .finally(() => {
            autoBusyRef.current[camera.id] = false;
          });
      });
    }, 5000);

    return () => window.clearInterval(interval);
  }, [activeCameras, hasModule]);

  function refreshCamera(cameraId: string) {
    setFeedVersions((current) => ({ ...current, [cameraId]: (current[cameraId] ?? 0) + 1 }));
  }

  function refreshAllFeeds() {
    setFeedVersions((current) => Object.fromEntries(activeCameras.map((camera) => [camera.id, (current[camera.id] ?? 0) + 1])));
  }

  function openFeed(camera: Camera) {
    const url = feedUrl(camera, feedVersions[camera.id] ?? 0);
    if (!url) return;
    window.open(url, "_blank", "noopener,noreferrer");
  }

  if (!loading && activeCameras.length === 0) {
    return (
      <EmptyState
        title="Add an active camera first"
        description="Zone View is common for Attendance and Object Detection. Add a camera source first, then return here."
        action={<Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>Add camera</Button>}
      />
    );
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Camera management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Zone View</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">All active camera feeds appear in a two-column grid. Snapshot images auto-refresh every 3 seconds. Click any feed to open it in a new tab.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadCameras()} disabled={loading}>Reload cameras</Button>
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={refreshAllFeeds} disabled={!activeCameras.length}>Refresh all feeds</Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>Add camera</Button>
          </div>
        </div>
      </section>

      <section className="grid items-start gap-6 md:grid-cols-2">
        {activeCameras.map((camera) => {
          const previewUrl = feedUrl(camera, feedVersions[camera.id] ?? 0);
          return (
            <Card key={camera.id}>
              <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-semibold">{camera.name}</h2>
                  <p className="text-sm text-slate-500">{camera.camera_type.replace("_", " ")}</p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge tone={camera.health_status === "online" ? "success" : "neutral"}>{camera.health_status}</Badge>
                  <Button size="sm" variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => refreshCamera(camera.id)}>Refresh feed</Button>
                  <Button size="sm" variant="ghost" leftIcon={<ExternalLink className="h-4 w-4" />} onClick={() => openFeed(camera)} disabled={!previewUrl}>Fullscreen</Button>
                </div>
              </div>

              <button type="button" className="relative block aspect-video w-full overflow-hidden rounded-2xl bg-slate-950 text-left" onClick={() => openFeed(camera)} disabled={!previewUrl}>
                {previewUrl ? (
                  <img src={previewUrl} alt={`${camera.name} feed`} className="absolute inset-0 h-full w-full object-cover" />
                ) : (
                  <div className="grid h-full place-items-center text-center text-slate-400"><div><Video className="mx-auto h-9 w-9" /><p className="mt-2 text-sm">No browser-compatible HTTP stream or snapshot URL.</p></div></div>
                )}
              </button>
              <p className="mt-3 text-xs text-slate-500">HTTP MJPEG and Phone IP Webcam streams preview directly. RTSP requires a browser-compatible gateway.</p>
              {hasModule("attendance") && (camera.assigned_feature_scope === "attendance" || camera.assigned_feature_scope === "both") ? (
                <div className="mt-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-600 dark:bg-white/5 dark:text-slate-300">
                  Auto recognition: {autoStatus[camera.id]?.running ? "running" : autoStatus[camera.id]?.label ?? "waiting"}
                  {autoStatus[camera.id]?.updated_at ? ` | ${formatClockTime(autoStatus[camera.id].updated_at)}` : ""}
                </div>
              ) : null}
            </Card>
          );
        })}
      </section>

      {message ? <div className="fixed right-4 top-4 z-50"><Toast tone={message.tone} title={message.title} message={message.message} onClose={() => setMessage(null)} /></div> : null}
    </div>
  );
}

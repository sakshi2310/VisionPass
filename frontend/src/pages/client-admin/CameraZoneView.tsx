import { Loader2, Plus, Save, Trash2, Video } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  fetchCameras,
  updateCamera,
  type Camera,
  type CameraDetectionZone,
} from "@/services/clientAdminAttendance";

function clamp(value: number, minimum: number, maximum: number) {
  return Math.min(maximum, Math.max(minimum, value));
}

export function CameraZoneViewPage() {
  const navigate = useNavigate();
  const { user } = useApp();
  const basePath = user?.role === "TENANT_ADMIN" ? "/tenant-admin" : "/client-admin";
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [zones, setZones] = useState<CameraDetectionZone[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ tone: "success" | "error"; title: string; message: string } | null>(null);

  usePageTitle("Vision Pass | Camera Zone View");

  const eligibleCameras = useMemo(
    () => cameras.filter((camera) => camera.assigned_feature_scope !== "attendance"),
    [cameras],
  );
  const selectedCamera = eligibleCameras.find((camera) => camera.id === selectedId) ?? null;
  const previewUrl = selectedCamera?.stream_url?.startsWith("http")
    ? selectedCamera.stream_url
    : selectedCamera?.snapshot_url ?? "";

  useEffect(() => {
    async function load() {
      try {
        const response = await fetchCameras();
        setCameras(response);
        const eligible = response.filter((camera) => camera.assigned_feature_scope !== "attendance");
        if (eligible.length) setSelectedId(eligible[0].id);
      } catch (error) {
        setMessage({ tone: "error", title: "Cameras unavailable", message: error instanceof Error ? error.message : "Unable to load cameras." });
      } finally {
        setLoading(false);
      }
    }
    void load();
  }, []);

  useEffect(() => {
    setZones(selectedCamera?.detection_zones ?? []);
  }, [selectedCamera?.id]);

  function addZone() {
    const number = zones.length + 1;
    setZones((current) => [
      ...current,
      { id: crypto.randomUUID(), name: `Zone ${number}`, x: 10, y: 10, width: 35, height: 35 },
    ]);
  }

  function updateZone(id: string, patch: Partial<CameraDetectionZone>) {
    setZones((current) =>
      current.map((zone) => {
        if (zone.id !== id) return zone;
        const next = { ...zone, ...patch };
        next.x = clamp(next.x, 0, 99);
        next.y = clamp(next.y, 0, 99);
        next.width = clamp(next.width, 1, 100 - next.x);
        next.height = clamp(next.height, 1, 100 - next.y);
        return next;
      }),
    );
  }

  async function saveZones() {
    if (!selectedCamera) return;
    try {
      setSaving(true);
      const updated = await updateCamera(selectedCamera.id, { detection_zones: zones });
      setCameras((current) => current.map((camera) => (camera.id === updated.id ? updated : camera)));
      setMessage({ tone: "success", title: "Zones saved", message: `${zones.length} detection zone${zones.length === 1 ? "" : "s"} saved for ${selectedCamera.name}.` });
    } catch (error) {
      setMessage({ tone: "error", title: "Save failed", message: error instanceof Error ? error.message : "Unable to save zones." });
    } finally {
      setSaving(false);
    }
  }

  if (!loading && eligibleCameras.length === 0) {
    return (
      <EmptyState
        title="Add an Object Detection camera first"
        description="Create a camera and assign it to Object Detection or Both. It will then appear in Zone View."
        action={<Button leftIcon={<Plus className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>Add camera</Button>}
      />
    );
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Object detection</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Camera Zone View</h1>
            <p className="mt-2 text-sm text-slate-400">View the stream and define percentage-based regions of interest for detection.</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" leftIcon={<Plus className="h-4 w-4" />} onClick={() => navigate(`${basePath}/cameras`)}>Add camera</Button>
            <Button leftIcon={saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} onClick={() => void saveZones()} disabled={!selectedCamera || saving}>Save zones</Button>
          </div>
        </div>
      </section>

      <Card>
        <label className="grid max-w-xl gap-2 text-sm font-medium">
          Camera
          <select value={selectedId} onChange={(event) => setSelectedId(event.target.value)} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900">
            {eligibleCameras.map((camera) => <option key={camera.id} value={camera.id}>{camera.name} · {camera.location}</option>)}
          </select>
        </label>
      </Card>

      <section className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
        <Card>
          <div className="mb-4 flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Stream preview</h2>
              <p className="text-sm text-slate-500">{selectedCamera?.name ?? "Select a camera"}</p>
            </div>
            <Badge tone={selectedCamera?.health_status === "online" ? "success" : "neutral"}>{selectedCamera?.health_status ?? "unknown"}</Badge>
          </div>
          <div className="relative aspect-video overflow-hidden rounded-2xl bg-slate-950">
            {previewUrl ? (
              <img src={previewUrl} alt="Camera stream" className="absolute inset-0 h-full w-full object-contain" />
            ) : (
              <div className="grid h-full place-items-center text-center text-slate-400"><div><Video className="mx-auto h-9 w-9" /><p className="mt-2 text-sm">No browser-compatible HTTP stream or snapshot URL.</p></div></div>
            )}
            {zones.map((zone) => (
              <div
                key={zone.id}
                className="pointer-events-none absolute border-2 border-cyan-400 bg-cyan-400/15"
                style={{ left: `${zone.x}%`, top: `${zone.y}%`, width: `${zone.width}%`, height: `${zone.height}%` }}
              >
                <span className="absolute left-0 top-0 bg-cyan-500 px-2 py-1 text-xs font-semibold text-slate-950">{zone.name}</span>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">HTTP MJPEG and Phone IP Webcam streams preview directly. RTSP requires a browser-compatible gateway.</p>
        </Card>

        <Card>
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Detection zones</h2>
              <p className="text-sm text-slate-500">Coordinates are percentages of the frame.</p>
            </div>
            <Button size="sm" variant="secondary" leftIcon={<Plus className="h-4 w-4" />} onClick={addZone}>Add zone</Button>
          </div>
          <div className="mt-5 grid gap-4">
            {zones.length === 0 ? <p className="rounded-2xl border border-dashed p-5 text-sm text-slate-500">No zones configured. Add one to mark a detection area.</p> : null}
            {zones.map((zone) => (
              <div key={zone.id} className="grid gap-3 rounded-2xl border border-slate-200 p-4 dark:border-white/10">
                <div className="flex items-center gap-2">
                  <input value={zone.name} onChange={(event) => updateZone(zone.id, { name: event.target.value })} className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-transparent px-3 py-2 font-medium dark:border-white/10" />
                  <Button size="sm" variant="danger" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => setZones((current) => current.filter((item) => item.id !== zone.id))}>Remove</Button>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {(["x", "y", "width", "height"] as const).map((field) => (
                    <label key={field} className="grid gap-1 text-xs uppercase text-slate-500">
                      {field} %
                      <input type="number" min={field === "width" || field === "height" ? 1 : 0} max="100" value={zone[field]} onChange={(event) => updateZone(zone.id, { [field]: Number(event.target.value) })} className="rounded-xl border border-slate-200 bg-transparent px-3 py-2 text-sm text-slate-900 dark:border-white/10 dark:text-white" />
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Card>
      </section>

      {message ? <div className="fixed right-4 top-4 z-50"><Toast {...message} onClose={() => setMessage(null)} /></div> : null}
    </div>
  );
}

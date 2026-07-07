import { Camera as CameraIcon, Eye, Loader2, Pencil, Plus, RefreshCw, Save, TestTube2, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { Toast } from "@/components/ui/Toast";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  createCamera,
  deleteCamera,
  fetchCameras,
  fetchCameraSnapshot,
  testCamera,
  updateCamera,
  type Camera,
  type CameraPayload,
} from "@/services/clientAdminAttendance";

type Draft = {
  name: string;
  location: string;
  camera_type: Camera["camera_type"];
  phone_ip: string;
  port: string;
  stream_url: string;
  snapshot_url: string;
  assigned_feature_scope: Camera["assigned_feature_scope"];
  username: string;
  password: string;
  is_active: boolean;
};

const emptyDraft: Draft = {
  name: "",
  location: "",
  camera_type: "phone_ip_webcam",
  phone_ip: "",
  port: "8080",
  stream_url: "",
  snapshot_url: "",
  assigned_feature_scope: "both",
  username: "",
  password: "",
  is_active: true,
};

function fromCamera(camera: Camera): Draft {
  return {
    name: camera.name,
    location: camera.location,
    camera_type: camera.camera_type,
    phone_ip: camera.phone_ip ?? "",
    port: camera.port?.toString() ?? "",
    stream_url: camera.stream_url ?? "",
    snapshot_url: camera.snapshot_url ?? "",
    assigned_feature_scope: camera.assigned_feature_scope,
    username: camera.username ?? "",
    password: "",
    is_active: camera.is_active,
  };
}

function healthTone(health: Camera["health_status"]) {
  if (health === "online") return "success" as const;
  if (health === "offline" || health === "error") return "danger" as const;
  return "neutral" as const;
}

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

export function CamerasPage() {
  const navigate = useNavigate();
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [editing, setEditing] = useState<Camera | null | "new">(null);
  const [draft, setDraft] = useState<Draft>(emptyDraft);
  const [snapshotUrl, setSnapshotUrl] = useState("");
  const [snapshotCamera, setSnapshotCamera] = useState<Camera | null>(null);
  const [toast, setToast] = useState<ToastState>(null);

  usePageTitle("Vision Pass | Cameras");

  async function loadCameras() {
    try {
      setLoading(true);
      setCameras(await fetchCameras());
    } catch (error) {
      setToast({ tone: "error", title: "Load failed", message: error instanceof Error ? error.message : "Unable to load cameras." });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadCameras();
  }, []);

  useEffect(() => {
    return () => {
      if (snapshotUrl) URL.revokeObjectURL(snapshotUrl);
    };
  }, [snapshotUrl]);

  function openCreate() {
    setDraft(emptyDraft);
    setEditing("new");
  }

  function openEdit(camera: Camera) {
    setDraft(fromCamera(camera));
    setEditing(camera);
  }

  function closeEditor() {
    setEditing(null);
    setDraft(emptyDraft);
  }

  async function saveCamera(event: FormEvent) {
    event.preventDefault();
    if (!draft.name.trim()) {
      setToast({ tone: "error", title: "Missing details", message: "Camera name is required." });
      return;
    }
    if (["ip_webcam", "phone_ip_webcam", "manual_snapshot"].includes(draft.camera_type) && !draft.snapshot_url.trim()) {
      setToast({ tone: "error", title: "Snapshot URL required", message: "This camera source needs an HTTP snapshot URL." });
      return;
    }
    if (draft.camera_type === "rtsp" && !draft.stream_url.trim()) {
      setToast({ tone: "error", title: "Stream URL required", message: "RTSP cameras need an RTSP stream URL." });
      return;
    }
    const payload: CameraPayload = {
      name: draft.name.trim(),
      location: draft.location.trim() || "Default",
      camera_type: draft.camera_type,
      phone_ip: draft.phone_ip.trim() || null,
      port: draft.port ? Number(draft.port) : null,
      stream_url: draft.stream_url.trim() || null,
      snapshot_url: draft.snapshot_url.trim() || null,
      assigned_feature_scope: draft.assigned_feature_scope || "both",
      username: draft.username.trim() || null,
      password: draft.password || null,
      is_active: draft.is_active,
    };
    try {
      setBusyId(editing === "new" ? "new" : editing?.id ?? "");
      if (editing === "new") await createCamera(payload);
      else if (editing) await updateCamera(editing.id, payload);
      closeEditor();
      await loadCameras();
      setToast({ tone: "success", title: "Camera saved", message: "Camera configuration was saved securely." });
    } catch (error) {
      setToast({ tone: "error", title: "Save failed", message: error instanceof Error ? error.message : "Unable to save camera." });
    } finally {
      setBusyId("");
    }
  }

  async function handleTest(camera: Camera) {
    try {
      setBusyId(camera.id);
      const result = await testCamera(camera.id);
      await loadCameras();
      setToast({ tone: "success", title: "Camera online", message: `${result.message} ${result.width} × ${result.height}` });
    } catch (error) {
      await loadCameras();
      setToast({ tone: "error", title: "Camera test failed", message: error instanceof Error ? error.message : "Camera could not be reached." });
    } finally {
      setBusyId("");
    }
  }

  async function handleSnapshot(camera: Camera) {
    try {
      setBusyId(camera.id);
      const blob = await fetchCameraSnapshot(camera.id);
      const url = URL.createObjectURL(blob);
      setSnapshotUrl(url);
      setSnapshotCamera(camera);
      await loadCameras();
    } catch (error) {
      setToast({ tone: "error", title: "Snapshot failed", message: error instanceof Error ? error.message : "Unable to fetch snapshot." });
    } finally {
      setBusyId("");
    }
  }

  async function handleDelete(camera: Camera) {
    if (!window.confirm(`Delete camera “${camera.name}”? This cannot be undone.`)) return;
    try {
      setBusyId(camera.id);
      await deleteCamera(camera.id);
      await loadCameras();
      setToast({ tone: "success", title: "Camera deleted", message: `${camera.name} was removed.` });
    } catch (error) {
      setToast({ tone: "error", title: "Delete failed", message: error instanceof Error ? error.message : "Unable to delete camera." });
    } finally {
      setBusyId("");
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Camera management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Configure camera sources</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">Common camera management for Attendance and Object Detection, including Android Phone IP Webcam.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className="h-4 w-4" />} onClick={() => void loadCameras()} disabled={loading}>Refresh</Button>
            <Button variant="secondary" leftIcon={<Eye className="h-4 w-4" />} onClick={() => navigate("zones")}>Zone View</Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openCreate}>Add camera</Button>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card className="p-4"><div className="text-sm text-slate-500">Total cameras</div><div className="mt-2 text-3xl font-semibold">{cameras.length}</div></Card>
        <Card className="p-4"><div className="text-sm text-slate-500">Online</div><div className="mt-2 text-3xl font-semibold text-emerald-500">{cameras.filter((camera) => camera.health_status === "online").length}</div></Card>
        <Card className="p-4"><div className="text-sm text-slate-500">Active</div><div className="mt-2 text-3xl font-semibold">{cameras.filter((camera) => camera.is_active).length}</div></Card>
      </section>

      <DataTable
        title="Configured cameras"
        subtitle="Credentials are encrypted and never displayed."
        headers={["Camera", "Type", "Snapshot / Stream", "Health", "Actions"]}
        emptyState={!loading && cameras.length === 0 ? <div className="p-6"><EmptyState title="No cameras configured" description="Add an IP Webcam or another camera source." action={<CameraIcon className="h-6 w-6 text-slate-400" />} /></div> : undefined}
      >
        {cameras.map((camera) => (
          <tr key={camera.id}>
            <td className="px-5 py-4"><div className="font-medium text-slate-900 dark:text-white">{camera.name}</div><div className="text-xs text-slate-500">{camera.location}</div></td>
            <td className="px-5 py-4 text-sm capitalize">{camera.camera_type.replace("_", " ")}</td>
            <td className="max-w-xs truncate px-5 py-4 text-xs text-slate-500">{camera.snapshot_url ?? camera.stream_url ?? "Local device"}</td>
            <td className="px-5 py-4"><Badge tone={healthTone(camera.health_status)}>{camera.health_status}</Badge></td>
            <td className="px-5 py-4">
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" leftIcon={busyId === camera.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <TestTube2 className="h-4 w-4" />} onClick={() => void handleTest(camera)} disabled={!!busyId || !camera.snapshot_url}>Test</Button>
                <Button size="sm" variant="ghost" leftIcon={<Eye className="h-4 w-4" />} onClick={() => void handleSnapshot(camera)} disabled={!!busyId || !camera.snapshot_url}>Snapshot</Button>
                <Button size="sm" variant="ghost" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(camera)} disabled={!!busyId}>Edit</Button>
                <Button size="sm" variant="danger" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void handleDelete(camera)} disabled={!!busyId}>Delete</Button>
              </div>
            </td>
          </tr>
        ))}
      </DataTable>

      <Modal
        open={editing !== null}
        title={editing === "new" ? "Add camera" : "Edit camera"}
        description="Passwords are encrypted at rest. Leave the password blank while editing to keep the existing value."
        onClose={closeEditor}
        footer={<div className="flex justify-end gap-2"><Button variant="secondary" onClick={closeEditor}>Cancel</Button><Button leftIcon={busyId ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} type="submit" form="camera-form" disabled={!!busyId}>Save camera</Button></div>}
      >
        <form id="camera-form" className="grid gap-4 md:grid-cols-2" onSubmit={(event) => void saveCamera(event)}>
          <label className="grid gap-1 text-sm md:col-span-2">Name<input className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} /></label>
          <label className="grid gap-1 text-sm">
            Camera source type
            <select className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.camera_type} onChange={(event) => setDraft({ ...draft, camera_type: event.target.value as Camera["camera_type"] })}>
              <option value="rtsp">RTSP Camera</option>
              <option value="http_mjpeg">HTTP MJPEG Stream</option>
              <option value="phone_ip_webcam">Phone IP Webcam</option>
              <option value="manual_snapshot">Manual Snapshot URL</option>
            </select>
          </label>
          {draft.camera_type === "phone_ip_webcam" ? (
            <>
              <label className="grid gap-1 text-sm">Phone IP address<input placeholder="192.168.1.20" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.phone_ip} onChange={(event) => setDraft({ ...draft, phone_ip: event.target.value })} /></label>
              <label className="grid gap-1 text-sm">Port<input type="number" min="1" max="65535" placeholder="8080" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.port} onChange={(event) => setDraft({ ...draft, port: event.target.value })} /></label>
              <div className="md:col-span-2">
                <Button type="button" variant="secondary" onClick={() => {
                  const base = `http://${draft.phone_ip || "PHONE_IP"}:${draft.port || "8080"}`;
                  setDraft({ ...draft, stream_url: `${base}/video`, snapshot_url: `${base}/shot.jpg` });
                }}>Use Android IP Webcam URLs</Button>
                <p className="mt-2 text-xs text-slate-500">Stream: http://PHONE_IP:PORT/video · Snapshot: http://PHONE_IP:PORT/shot.jpg</p>
              </div>
            </>
          ) : null}
          <label className="flex items-center gap-3 pt-7 text-sm"><input type="checkbox" checked={draft.is_active} onChange={(event) => setDraft({ ...draft, is_active: event.target.checked })} />Active camera</label>
          <label className="grid gap-1 text-sm md:col-span-2">Snapshot URL<input placeholder="http://192.168.1.20:8080/shot.jpg" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.snapshot_url} onChange={(event) => setDraft({ ...draft, snapshot_url: event.target.value })} /></label>
          <label className="grid gap-1 text-sm md:col-span-2">Stream URL<input placeholder="rtsp://camera.local/stream or http://.../video" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.stream_url} onChange={(event) => setDraft({ ...draft, stream_url: event.target.value })} /></label>
          <label className="grid gap-1 text-sm">Username<input autoComplete="off" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.username} onChange={(event) => setDraft({ ...draft, username: event.target.value })} /></label>
          <label className="grid gap-1 text-sm">Password<input type="password" autoComplete="new-password" className="rounded-2xl border border-slate-200 bg-white px-4 py-3 dark:border-white/10 dark:bg-slate-900" value={draft.password} onChange={(event) => setDraft({ ...draft, password: event.target.value })} /></label>
        </form>
      </Modal>

      <Modal open={snapshotCamera !== null} title={snapshotCamera ? `${snapshotCamera.name} snapshot` : "Camera snapshot"} onClose={() => { setSnapshotCamera(null); setSnapshotUrl(""); }}>
        {snapshotUrl ? <img src={snapshotUrl} alt="Camera snapshot" className="mx-auto max-h-[65vh] rounded-2xl object-contain" /> : null}
      </Modal>

      {toast ? <div className="fixed right-4 top-4 z-50"><Toast tone={toast.tone} title={toast.title} message={toast.message} onClose={() => setToast(null)} /></div> : null}
    </div>
  );
}

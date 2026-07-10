import { ArrowUpRight, CheckCircle2, Loader2, RefreshCw, ScanFace, UserPlus, UserX } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { Input } from "@/components/ui/Input";
import { usePageTitle } from "@/hooks/usePageTitle";
import { fetchCameras, type Camera } from "@/services/clientAdminAttendance";
import { personDetectionsApi, type PersonDetection } from "@/services/personDetections";
import { formatDate, formatTime } from "@/utils/format";

function matchTone(matchType: PersonDetection["match_type"]): "success" | "warning" | "neutral" {
  if (matchType === "staff") return "success";
  if (matchType === "visitor") return "warning";
  return "neutral";
}

function statusTone(status: PersonDetection["status"]): "success" | "warning" | "neutral" | "danger" | "info" {
  if (status === "new") return "warning";
  if (status === "reviewed") return "success";
  if (status === "converted_to_staff") return "success";
  if (status === "ignored") return "neutral";
  return "info";
}

function formatDuration(firstSeenAt: string, lastSeenAt: string) {
  const start = new Date(firstSeenAt).getTime();
  const end = new Date(lastSeenAt).getTime();
  if (!Number.isFinite(start) || !Number.isFinite(end) || end < start) {
    return "-";
  }
  const totalSeconds = Math.max(0, Math.round((end - start) / 1000));
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const seconds = totalSeconds % 60;
  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  if (minutes > 0) {
    return `${minutes}m ${seconds.toString().padStart(2, "0")}s`;
  }
  return `${seconds}s`;
}

export function PersonDetectionPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [detections, setDetections] = useState<PersonDetection[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [photoUrls, setPhotoUrls] = useState<Record<string, string>>({});
  const [noteOpen, setNoteOpen] = useState(false);
  const [noteTarget, setNoteTarget] = useState<PersonDetection | null>(null);
  const [noteValue, setNoteValue] = useState("");
  const [savingNote, setSavingNote] = useState(false);
  const [visitorOpen, setVisitorOpen] = useState(false);
  const [visitorTarget, setVisitorTarget] = useState<PersonDetection | null>(null);
  const [visitorName, setVisitorName] = useState("");
  const [visitorPhone, setVisitorPhone] = useState("");
  const [visitorPurpose, setVisitorPurpose] = useState("");
  const [visitorNotes, setVisitorNotes] = useState("");
  const [savingVisitor, setSavingVisitor] = useState(false);

  usePageTitle("Vision Pass | Person Detection");

  const camerasById = useMemo(() => new Map(cameras.map((camera) => [camera.id, camera])), [cameras]);
  const basePath = location.pathname.startsWith("/tenant-admin") ? "/tenant-admin" : "/client-admin";

  const load = useCallback(async () => {
    setLoading(true);
      setError("");
      try {
        const [nextDetections, nextCameras] = await Promise.all([
          personDetectionsApi.list({ limit: 200 }),
          fetchCameras(),
        ]);
        setDetections(nextDetections);
        setCameras(nextCameras);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Person detections could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const nextUrls: Record<string, string> = {};
    let cancelled = false;

    void (async () => {
      const rows = detections.filter((detection) => detection.image_path);
      const entries = await Promise.all(
        rows.map(async (detection) => {
          try {
            const blob = await personDetectionsApi.fetchPhotoBlob(detection.id);
            return [detection.id, URL.createObjectURL(blob)] as const;
          } catch {
            return [detection.id, ""] as const;
          }
        }),
      );
      if (cancelled) return;
      entries.forEach(([id, url]) => {
        if (url) nextUrls[id] = url;
      });
      setPhotoUrls((current) => {
        Object.values(current).forEach((url) => {
          if (!Object.values(nextUrls).includes(url)) URL.revokeObjectURL(url);
        });
        return nextUrls;
      });
    })();

    return () => {
      cancelled = true;
    };
  }, [detections]);

  useEffect(() => {
    return () => {
      Object.values(photoUrls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [photoUrls]);

  function openNote(detection: PersonDetection) {
    setNoteTarget(detection);
    setNoteValue(detection.note ?? "");
    setNoteOpen(true);
  }

  function openVisitor(detection: PersonDetection) {
    setVisitorTarget(detection);
    setVisitorName("");
    setVisitorPhone("");
    setVisitorPurpose("");
    setVisitorNotes(detection.note ?? "");
    setVisitorOpen(true);
  }

  async function saveNote() {
    if (!noteTarget) return;
    setSavingNote(true);
    setError("");
    try {
      await personDetectionsApi.note(noteTarget.id, noteValue.trim());
      setNoteOpen(false);
      setNoteTarget(null);
      setNoteValue("");
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Note could not be saved.");
    } finally {
      setSavingNote(false);
    }
  }

  async function saveVisitor() {
    if (!visitorTarget) return;
    setSavingVisitor(true);
    setError("");
    try {
      const response = await personDetectionsApi.addVisitor(visitorTarget.id, {
        name: visitorName.trim() || undefined,
        phone: visitorPhone.trim() || undefined,
        purpose: visitorPurpose.trim() || undefined,
        notes: visitorNotes.trim() || undefined,
      });
      const visitorId = String((response.visitor as Record<string, unknown>).id ?? "");
      setVisitorOpen(false);
      setVisitorTarget(null);
      if (visitorId) {
        navigate(`${basePath}/visitor-unknown/visitors/${visitorId}`);
      } else {
        await load();
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Visitor could not be created.");
    } finally {
      setSavingVisitor(false);
    }
  }

  async function ignoreDetection(detection: PersonDetection) {
    setBusyId(detection.id);
    setError("");
    try {
      await personDetectionsApi.ignore(detection.id);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Detection could not be ignored.");
    } finally {
      setBusyId("");
    }
  }

  async function refreshRowData() {
    await load();
  }

  const emptyMessage = "Show all camera-detected people here once snapshots start coming in.";

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Visitor + Unknown</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Person Detection</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Show all camera-detected people, with staff, visitor, and unknown classification from the live camera pipeline.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void refreshRowData()} disabled={loading}>
            Refresh
          </Button>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600">{error}</div> : null}

      {loading ? (
        <Card className="h-40 animate-pulse bg-slate-100 dark:bg-white/5" />
      ) : detections.length === 0 ? (
        <EmptyState
          title="No detections yet"
          description={emptyMessage}
          action={<ScanFace className="h-7 w-7 text-slate-400" />}
        />
      ) : (
        <DataTable
          headers={[
            "Photo",
            "First Seen",
            "Last Seen",
            "Duration",
            "Seen Count",
            "Detected Time",
            "Camera",
            "Zone",
            "Match Type",
            "Status",
            "Note",
            "Actions",
          ]}
        >
          {detections.map((detection) => {
            const camera = camerasById.get(detection.camera_id);
            const photoUrl = photoUrls[detection.id];
            const isUnknown = detection.match_type === "unknown";
            return (
              <tr key={detection.id}>
                <td className="px-5 py-4">
                  {photoUrl ? (
                    <img
                      src={photoUrl}
                      alt="Detected person"
                      className="h-16 w-16 rounded-2xl border border-slate-200 object-cover dark:border-white/10"
                    />
                  ) : (
                    <div className="grid h-16 w-16 place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-400 dark:border-white/10 dark:bg-white/5">
                      <ScanFace className="h-5 w-5" />
                    </div>
                  )}
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{formatDate(detection.first_seen_at)}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatTime(detection.first_seen_at)}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{formatDate(detection.last_seen_at)}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatTime(detection.last_seen_at)}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <span className="font-medium text-slate-900 dark:text-white">{formatDuration(detection.first_seen_at, detection.last_seen_at)}</span>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <span className="font-medium text-slate-900 dark:text-white">{detection.seen_count}</span>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{formatDate(detection.detected_at)}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatTime(detection.detected_at)}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{camera?.name ?? detection.camera_id}</div>
                  <div className="mt-1 text-xs text-slate-500">{camera?.location ?? "Camera"}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-500">{detection.zone_id ?? "-"}</td>
                <td className="px-5 py-4">
                  {detection.match_type === "staff" && detection.matched_staff_id ? (
                    <Link
                      to={`${basePath}/attendance/employees/${detection.matched_staff_id}`}
                      className="inline-flex"
                    >
                      <Badge tone={matchTone(detection.match_type)}>Staff</Badge>
                    </Link>
                  ) : (
                    <Badge tone={matchTone(detection.match_type)}>
                      {detection.match_type === "staff" ? "Staff" : detection.match_type === "visitor" ? "Visitor" : "Unknown"}
                    </Badge>
                  )}
                </td>
                <td className="px-5 py-4">
                  <Badge tone={statusTone(detection.status)}>{detection.status.replaceAll("_", " ")}</Badge>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{detection.note ?? "-"}</td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    {detection.match_type === "staff" && detection.matched_staff_id ? (
                      <Link
                        to={`${basePath}/attendance/employees/${detection.matched_staff_id}`}
                        className="inline-flex h-9 items-center justify-center gap-2 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 px-3 text-sm font-medium text-emerald-700 transition hover:border-emerald-500/30 hover:bg-emerald-500/15 dark:text-emerald-300"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                        View Staff Profile
                      </Link>
                    ) : null}
                    {detection.match_type === "visitor" && detection.matched_visitor_id ? (
                      <Link
                        to={`${basePath}/visitor-unknown/visitors/${detection.matched_visitor_id}`}
                        className="inline-flex h-9 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100 dark:hover:border-white/20 dark:hover:bg-slate-900/80"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                        Visitor profile
                      </Link>
                    ) : null}
                    {isUnknown ? (
                      <>
                        <Button size="sm" variant="secondary" leftIcon={<UserPlus className="h-4 w-4" />} onClick={() => openVisitor(detection)}>
                          Add Visitor
                        </Button>
                        <Button size="sm" variant="secondary" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => openNote(detection)}>
                          Add Note
                        </Button>
                        <Button size="sm" variant="ghost" leftIcon={busyId === detection.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserX className="h-4 w-4" />} onClick={() => void ignoreDetection(detection)} disabled={busyId === detection.id}>
                          Ignore
                        </Button>
                      </>
                    ) : null}
                  </div>
                </td>
              </tr>
            );
          })}
        </DataTable>
      )}

      <Modal
        open={noteOpen}
        title="Add note"
        description={noteTarget ? `Add a note for detection ${noteTarget.id}.` : undefined}
        onClose={() => setNoteOpen(false)}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setNoteOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => void saveNote()} disabled={savingNote}>
              {savingNote ? "Saving..." : "Save note"}
            </Button>
          </div>
        }
        >
          <div className="grid gap-4">
            <Input
              label="Note"
              value={noteValue}
              onChange={(event) => setNoteValue(event.target.value)}
              placeholder="Add context for this detection"
            />
          </div>
      </Modal>

      <Modal
        open={visitorOpen}
        title="Add as visitor"
        description={visitorTarget ? `Convert detection ${visitorTarget.id} into a visitor.` : undefined}
        onClose={() => setVisitorOpen(false)}
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="secondary" onClick={() => setVisitorOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => void saveVisitor()} disabled={savingVisitor}>
              {savingVisitor ? "Creating..." : "Create visitor"}
            </Button>
          </div>
        }
      >
        <div className="grid gap-3">
          <Input label="Name" value={visitorName} onChange={(event) => setVisitorName(event.target.value)} placeholder="Visitor name" />
          <Input label="Phone" value={visitorPhone} onChange={(event) => setVisitorPhone(event.target.value)} placeholder="Phone number" />
          <Input label="Purpose" value={visitorPurpose} onChange={(event) => setVisitorPurpose(event.target.value)} placeholder="Purpose of visit" />
          <Input label="Notes" value={visitorNotes} onChange={(event) => setVisitorNotes(event.target.value)} placeholder="Additional notes" />
        </div>
      </Modal>

    </div>
  );
}

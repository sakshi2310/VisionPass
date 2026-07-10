import { ArrowUpRight, CheckCircle2, Loader2, RefreshCw, ScanFace, UserPlus, UserX, AlertTriangle } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { usePageTitle } from "@/hooks/usePageTitle";
import { fetchCameras, type Camera } from "@/services/clientAdminAttendance";
import { personDetectionsApi, unknownReviewApi, type PersonDetection } from "@/services/personDetections";
import { formatDate, formatTime } from "@/utils/format";

function matchTone(matchType: PersonDetection["match_type"]): "success" | "warning" | "neutral" {
  if (matchType === "staff") return "success";
  if (matchType === "visitor") return "warning";
  return "neutral";
}

function statusTone(status: PersonDetection["status"]): "success" | "warning" | "neutral" | "danger" | "info" {
  if (status === "new") return "warning";
  if (status === "reviewed") return "success";
  if (status === "suspicious") return "danger";
  if (status === "ignored") return "neutral";
  return "info";
}

export function UnknownReviewPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [items, setItems] = useState<PersonDetection[]>([]);
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

  usePageTitle("Vision Pass | Unknown Review");

  const basePath = location.pathname.startsWith("/tenant-admin") ? "/tenant-admin" : "/client-admin";
  const camerasById = useMemo(() => new Map(cameras.map((camera) => [camera.id, camera])), [cameras]);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [rows, nextCameras] = await Promise.all([
        unknownReviewApi.list({ limit: 200 }),
        fetchCameras(),
      ]);
      setItems(rows);
      setCameras(nextCameras);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unknown review could not be loaded.");
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
      const rows = items.filter((item) => item.image_path);
      const entries = await Promise.all(
        rows.map(async (item) => {
          try {
            const blob = await personDetectionsApi.fetchPhotoBlob(item.id);
            return [item.id, URL.createObjectURL(blob)] as const;
          } catch {
            return [item.id, ""] as const;
          }
        }),
      );
      if (cancelled) return;
      entries.forEach(([id, url]) => {
        if (url) nextUrls[id] = url;
      });
      setPhotoUrls((current) => {
        Object.values(current).forEach((url) => URL.revokeObjectURL(url));
        return nextUrls;
      });
    })();
    return () => {
      cancelled = true;
      Object.values(nextUrls).forEach((url) => URL.revokeObjectURL(url));
    };
  }, [items]);

  function openNote(item: PersonDetection) {
    setNoteTarget(item);
    setNoteValue(item.note ?? "");
    setNoteOpen(true);
  }

  function openVisitor(item: PersonDetection) {
    setVisitorTarget(item);
    setVisitorName("");
    setVisitorPhone("");
    setVisitorPurpose("");
    setVisitorNotes(item.note ?? "");
    setVisitorOpen(true);
  }

  async function saveNote() {
    if (!noteTarget) return;
    setSavingNote(true);
    setError("");
    try {
      await unknownReviewApi.note(noteTarget.id, noteValue.trim());
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
      const response = await unknownReviewApi.addVisitor(visitorTarget.id, {
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

  async function markReviewed(item: PersonDetection) {
    setBusyId(item.id);
    setError("");
    try {
      await unknownReviewApi.markReviewed(item.id);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Detection could not be marked reviewed.");
    } finally {
      setBusyId("");
    }
  }

  async function markSuspicious(item: PersonDetection) {
    setBusyId(item.id);
    setError("");
    try {
      await unknownReviewApi.markSuspicious(item.id);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Detection could not be marked suspicious.");
    } finally {
      setBusyId("");
    }
  }

  async function ignore(item: PersonDetection) {
    setBusyId(item.id);
    setError("");
    try {
      await unknownReviewApi.ignore(item.id);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Detection could not be ignored.");
    } finally {
      setBusyId("");
    }
  }

  const counts = useMemo(() => {
    return items.reduce(
      (current, item) => {
        current.total += 1;
        if (item.status === "new") current.new += 1;
        if (item.status === "reviewed") current.reviewed += 1;
        return current;
      },
      { total: 0, new: 0, reviewed: 0 },
    );
  }, [items]);

  const emptyMessage = "Unknown detections with notes will appear here for review.";

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Visitor + Unknown</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Unknown Review</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-400">
              Review unknown detections where a note was added, then mark them reviewed, suspicious, ignored, or convert them into visitors.
            </p>
          </div>
          <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>
            Refresh
          </Button>
        </div>
      </section>

      <section className="grid gap-4 sm:grid-cols-3">
        {[
          ["Total notes", counts.total],
          ["New", counts.new],
          ["Reviewed", counts.reviewed],
        ].map(([label, value]) => (
          <Card key={label as string} className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">{label}</p>
              <p className="mt-2 text-3xl font-semibold text-slate-900 dark:text-white">{loading ? "..." : value}</p>
            </div>
            <div className="rounded-2xl bg-cyan-500/10 p-3 text-cyan-500">
              <ScanFace className="h-5 w-5" />
            </div>
          </Card>
        ))}
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600">{error}</div> : null}

      {loading ? (
        <Card className="h-40 animate-pulse bg-slate-100 dark:bg-white/5" />
      ) : items.length === 0 ? (
        <EmptyState title="No unknown review items" description={emptyMessage} action={<ScanFace className="h-7 w-7 text-slate-400" />} />
      ) : (
        <DataTable headers={["Photo", "Detected Time", "Camera", "Zone", "Note", "Status", "Actions"]}>
          {items.map((item) => {
            const camera = camerasById.get(item.camera_id);
            const photoUrl = photoUrls[item.id];
            return (
              <tr key={item.id}>
                <td className="px-5 py-4">
                  {photoUrl ? (
                    <img src={photoUrl} alt="Detected person" className="h-16 w-16 rounded-2xl border border-slate-200 object-cover dark:border-white/10" />
                  ) : (
                    <div className="grid h-16 w-16 place-items-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-slate-400 dark:border-white/10 dark:bg-white/5">
                      <ScanFace className="h-5 w-5" />
                    </div>
                  )}
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{formatDate(item.detected_at)}</div>
                  <div className="mt-1 text-xs text-slate-500">{formatTime(item.detected_at)}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">
                  <div className="font-medium text-slate-900 dark:text-white">{camera?.name ?? item.camera_id}</div>
                  <div className="mt-1 text-xs text-slate-500">{camera?.location ?? "Camera"}</div>
                </td>
                <td className="px-5 py-4 text-sm text-slate-500">{item.zone_id ?? "-"}</td>
                <td className="px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{item.note ?? "-"}</td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    <Badge tone={matchTone(item.match_type)}>{item.match_type === "staff" ? "Staff" : item.match_type === "visitor" ? "Visitor" : "Unknown"}</Badge>
                    <Badge tone={statusTone(item.status)}>{item.status.replaceAll("_", " ")}</Badge>
                  </div>
                </td>
                <td className="px-5 py-4">
                  <div className="flex flex-wrap gap-2">
                    {item.match_type === "visitor" && item.matched_visitor_id ? (
                      <Link
                        to={`${basePath}/visitor-unknown/visitors/${item.matched_visitor_id}`}
                        className="inline-flex h-9 items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50 dark:border-white/10 dark:bg-slate-950/50 dark:text-slate-100 dark:hover:border-white/20 dark:hover:bg-slate-900/80"
                      >
                        <ArrowUpRight className="h-4 w-4" />
                        Visitor profile
                      </Link>
                    ) : null}
                    <Button size="sm" variant="secondary" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => openNote(item)}>
                      Edit Note
                    </Button>
                    <Button size="sm" variant="secondary" leftIcon={<UserPlus className="h-4 w-4" />} onClick={() => openVisitor(item)}>
                      Add as Visitor
                    </Button>
                    <Button size="sm" variant="secondary" leftIcon={<CheckCircle2 className="h-4 w-4" />} onClick={() => void markReviewed(item)} disabled={busyId === item.id}>
                      Mark Reviewed
                    </Button>
                    <Button size="sm" variant="secondary" leftIcon={<AlertTriangle className="h-4 w-4" />} onClick={() => void markSuspicious(item)} disabled={busyId === item.id}>
                      Mark Suspicious
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      leftIcon={busyId === item.id ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserX className="h-4 w-4" />}
                      onClick={() => void ignore(item)}
                      disabled={busyId === item.id}
                    >
                      Ignore
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </DataTable>
      )}

      <Modal
        open={noteOpen}
        title="Edit note"
        description={noteTarget ? `Update the note for detection ${noteTarget.id}.` : undefined}
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
        <Input label="Note" value={noteValue} onChange={(event) => setNoteValue(event.target.value)} placeholder="Add context for this detection" />
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

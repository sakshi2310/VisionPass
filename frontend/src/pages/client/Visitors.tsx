import { History, LogIn, LogOut, Pencil, Plus, RefreshCw, Trash2 } from "lucide-react";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { DataTable } from "@/components/ui/DataTable";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { usePageTitle } from "@/hooks/usePageTitle";
import {
  visitorsApi,
  type Visitor,
  type VisitorDetail,
  type VisitorPayload,
  type VisitorStatus,
} from "@/services/visitors";
import { formatDate, formatTime } from "@/utils/format";

const blank: VisitorPayload = {
  full_name: "",
  phone: "",
  email: "",
  company: "",
  purpose: "",
  host_employee_id: null,
  photo_path: null,
  status: "expected",
};

function tone(status: VisitorStatus): "info" | "success" | "neutral" | "danger" {
  if (status === "expected") return "info";
  if (status === "checked_in") return "success";
  if (status === "blocked") return "danger";
  return "neutral";
}

export function Visitors() {
  const [items, setItems] = useState<Visitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState("");
  const [error, setError] = useState("");
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<Visitor | null>(null);
  const [form, setForm] = useState<VisitorPayload>(blank);
  const [saving, setSaving] = useState(false);
  const [history, setHistory] = useState<VisitorDetail | null>(null);
  usePageTitle("Vision Pass | Visitors");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try { setItems(await visitorsApi.list()); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Visitors could not be loaded."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => void load(), [load]);

  function openAdd() {
    setEditing(null);
    setForm(blank);
    setFormOpen(true);
  }

  function openEdit(visitor: Visitor) {
    setEditing(visitor);
    setForm({
      full_name: visitor.full_name,
      phone: visitor.phone,
      email: visitor.email ?? "",
      company: visitor.company ?? "",
      purpose: visitor.purpose,
      host_employee_id: visitor.host_employee_id ?? null,
      photo_path: visitor.photo_path ?? null,
      status: visitor.status,
    });
    setFormOpen(true);
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        ...form,
        email: form.email || null,
        company: form.company || null,
        host_employee_id: form.host_employee_id || null,
        photo_path: form.photo_path || null,
      };
      editing ? await visitorsApi.update(editing.id, payload) : await visitorsApi.create(payload);
      setFormOpen(false);
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Visitor could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function action(visitor: Visitor, kind: "in" | "out") {
    setBusyId(visitor.id);
    setError("");
    try {
      kind === "in" ? await visitorsApi.checkIn(visitor.id) : await visitorsApi.checkOut(visitor.id);
      await load();
      if (history?.id === visitor.id) setHistory(await visitorsApi.get(visitor.id));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Visitor status could not be changed.");
    } finally {
      setBusyId("");
    }
  }

  async function viewHistory(visitor: Visitor) {
    setBusyId(visitor.id);
    try { setHistory(await visitorsApi.get(visitor.id)); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Visitor history could not be loaded."); }
    finally { setBusyId(""); }
  }

  async function remove(visitor: Visitor) {
    if (!window.confirm(`Delete ${visitor.full_name} and their visit history?`)) return;
    setBusyId(visitor.id);
    try { await visitorsApi.remove(visitor.id); await load(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "Visitor could not be deleted."); }
    finally { setBusyId(""); }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Visitor management</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Visitors</h1>
            <p className="mt-2 text-sm text-slate-400">Register guests, manage entry and exit, and review visit history.</p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" leftIcon={<RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />} onClick={() => void load()} disabled={loading}>Refresh</Button>
            <Button leftIcon={<Plus className="h-4 w-4" />} onClick={openAdd}>Add visitor</Button>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-600">{error}</div> : null}

      {loading ? <Card><div className="h-24 animate-pulse rounded-2xl bg-slate-100 dark:bg-white/5" /></Card> : items.length === 0 ? (
        <EmptyState title="No visitors registered" description="Add the first visitor to begin tracking visits." action={<Button onClick={openAdd}>Add visitor</Button>} />
      ) : (
        <DataTable headers={["Visitor", "Contact", "Purpose", "Status", "Updated", "Actions"]}>
          {items.map((visitor) => (
            <tr key={visitor.id}>
              <td className="px-5 py-4"><p className="font-medium text-slate-900 dark:text-white">{visitor.full_name}</p><p className="mt-1 text-xs text-slate-500">{visitor.company ?? "No company"}</p></td>
              <td className="px-5 py-4 text-sm"><p>{visitor.phone}</p><p className="text-xs text-slate-500">{visitor.email ?? "—"}</p></td>
              <td className="max-w-52 px-5 py-4 text-sm text-slate-600 dark:text-slate-300">{visitor.purpose}</td>
              <td className="px-5 py-4"><Badge tone={tone(visitor.status)}>{visitor.status.replace("_", " ")}</Badge></td>
              <td className="px-5 py-4 text-sm text-slate-500">{formatDate(visitor.updated_at)} {formatTime(visitor.updated_at)}</td>
              <td className="px-5 py-4">
                <div className="flex flex-wrap gap-2">
                  {visitor.status !== "checked_in" && visitor.status !== "blocked" ? <Button size="sm" variant="secondary" leftIcon={<LogIn className="h-4 w-4" />} onClick={() => void action(visitor, "in")} disabled={busyId === visitor.id}>Check in</Button> : null}
                  {visitor.status === "checked_in" ? <Button size="sm" variant="secondary" leftIcon={<LogOut className="h-4 w-4" />} onClick={() => void action(visitor, "out")} disabled={busyId === visitor.id}>Check out</Button> : null}
                  <Button size="sm" variant="ghost" leftIcon={<History className="h-4 w-4" />} onClick={() => void viewHistory(visitor)}>History</Button>
                  <Button size="sm" variant="ghost" leftIcon={<Pencil className="h-4 w-4" />} onClick={() => openEdit(visitor)}>Edit</Button>
                  <Button size="sm" variant="ghost" leftIcon={<Trash2 className="h-4 w-4" />} onClick={() => void remove(visitor)}>Delete</Button>
                </div>
              </td>
            </tr>
          ))}
        </DataTable>
      )}

      <Modal open={formOpen} title={editing ? "Edit visitor" : "Add visitor"} onClose={() => setFormOpen(false)}>
        <form className="grid gap-4" onSubmit={save}>
          <div className="grid gap-4 md:grid-cols-2">
            <Input required label="Full name" value={form.full_name} onChange={(event) => setForm({ ...form, full_name: event.target.value })} />
            <Input required label="Phone" value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            <Input type="email" label="Email" value={form.email ?? ""} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            <Input label="Company" value={form.company ?? ""} onChange={(event) => setForm({ ...form, company: event.target.value })} />
            <Input label="Host employee ID" value={form.host_employee_id ?? ""} onChange={(event) => setForm({ ...form, host_employee_id: event.target.value || null })} />
            <Input label="Photo path" value={form.photo_path ?? ""} onChange={(event) => setForm({ ...form, photo_path: event.target.value || null })} />
          </div>
          <Input required label="Purpose" value={form.purpose} onChange={(event) => setForm({ ...form, purpose: event.target.value })} />
          <label className="grid gap-2 text-sm font-medium text-slate-600 dark:text-slate-300">
            Status
            <select disabled={editing?.status === "checked_in"} className="h-11 rounded-2xl border border-slate-200 bg-white px-4 disabled:opacity-60 dark:border-white/10 dark:bg-slate-950" value={form.status} onChange={(event) => setForm({ ...form, status: event.target.value as VisitorStatus })}>
              <option value="expected">Expected</option>
              {editing?.status === "checked_in" ? <option value="checked_in">Checked in</option> : null}
              {editing?.status === "checked_out" ? <option value="checked_out">Checked out</option> : null}
              <option value="blocked">Blocked</option>
            </select>
          </label>
          <div className="flex justify-end gap-2"><Button variant="secondary" onClick={() => setFormOpen(false)}>Cancel</Button><Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save visitor"}</Button></div>
        </form>
      </Modal>

      <Modal open={Boolean(history)} title={history ? `${history.full_name} history` : "Visitor history"} onClose={() => setHistory(null)}>
        {history?.visits.length ? <div className="grid gap-3">{history.visits.map((visit) => (
          <div key={visit.id} className="rounded-2xl border border-slate-200 p-4 dark:border-white/10">
            <div className="flex items-center justify-between"><Badge tone={visit.check_out_time ? "neutral" : "success"}>{visit.check_out_time ? "completed" : "on site"}</Badge><span className="text-xs text-slate-500">{visit.access_status}</span></div>
            <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2"><p>Check-in: {formatDate(visit.check_in_time)} {formatTime(visit.check_in_time)}</p><p>Check-out: {visit.check_out_time ? `${formatDate(visit.check_out_time)} ${formatTime(visit.check_out_time)}` : "—"}</p></div>
            {visit.notes ? <p className="mt-3 text-sm text-slate-500">{visit.notes}</p> : null}
          </div>
        ))}</div> : <div className="rounded-2xl border border-dashed border-slate-200 p-8 text-center text-sm text-slate-500">No visit history yet.</div>}
      </Modal>
    </div>
  );
}

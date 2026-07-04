import { CheckCircle2, Loader2, Save } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Toast } from "@/components/ui/Toast";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { fetchAttendanceSettings, updateAttendanceSettings } from "@/services/clientAdminAttendance";

const dayLabels = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const timezoneOptions = ["Asia/Kolkata", "Asia/Calcutta", "UTC", "America/New_York", "Europe/London"];

type ToastState = {
  tone: "success" | "error";
  title: string;
  message: string;
} | null;

export function AttendanceSettingsPage() {
  const { currentTenant } = useApp();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [toast, setToast] = useState<ToastState>(null);
  const [settingsId, setSettingsId] = useState("");
  const [cooldown, setCooldown] = useState("5");
  const [allowManualCorrection, setAllowManualCorrection] = useState(true);
  const [requireCorrectionReason, setRequireCorrectionReason] = useState(true);
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [selectedDays, setSelectedDays] = useState<number[]>([1, 2, 3, 4, 5, 6]);

  usePageTitle("Vision Pass | Attendance Settings");

  useEffect(() => {
    let active = true;

    async function loadSettings() {
      try {
        setLoading(true);
        setError("");
        const response = await fetchAttendanceSettings();
        if (!active) return;
        setSettingsId(response.attendance_settings.id);
        setCooldown(String(response.attendance_settings.duplicate_detection_cooldown_minutes));
        setAllowManualCorrection(response.attendance_settings.allow_manual_correction);
        setRequireCorrectionReason(response.attendance_settings.require_correction_reason);
        setTimezone(response.attendance_settings.timezone || "Asia/Kolkata");
        setSelectedDays(
          response.working_days.filter((day) => day.is_working).map((day) => day.day_of_week).sort((a, b) => a - b),
        );
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Unable to load attendance settings.");
      } finally {
        if (active) setLoading(false);
      }
    }

    void loadSettings();

    return () => {
      active = false;
    };
  }, []);

  const workingDaySummary = useMemo(() => selectedDays.map((day) => dayLabels[day]).join(", "), [selectedDays]);

  function toggleDay(dayIndex: number) {
    setSelectedDays((current) =>
      current.includes(dayIndex) ? current.filter((day) => day !== dayIndex) : [...current, dayIndex].sort((a, b) => a - b),
    );
  }

  function validate() {
    const parsedCooldown = Number(cooldown);
    if (!Number.isInteger(parsedCooldown) || parsedCooldown < 1) {
      return "Duplicate detection cooldown must be at least 1 minute.";
    }
    if (selectedDays.length === 0) {
      return "Select at least one working day.";
    }
    if (!timezone.trim()) {
      return "Timezone is required.";
    }
    return "";
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = validate();
    if (message) {
      setToast({ tone: "error", title: "Validation error", message });
      return;
    }

    try {
      setSaving(true);
      setError("");
      const response = await updateAttendanceSettings({
        duplicate_detection_cooldown_minutes: Number(cooldown),
        allow_manual_correction: allowManualCorrection,
        require_correction_reason: requireCorrectionReason,
        timezone: timezone.trim(),
        working_days: selectedDays,
      });
      setSettingsId(response.attendance_settings.id);
      setToast({
        tone: "success",
        title: "Attendance settings saved",
        message: `Working days updated for ${currentTenant?.name ?? "the current tenant"}.`,
      });
    } catch (err) {
      setToast({
        tone: "error",
        title: "Save failed",
        message: err instanceof Error ? err.message : "Unable to save attendance settings.",
      });
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Attendance settings</p>
            <h1 className="mt-2 text-3xl font-semibold text-white">Configure attendance rules for this tenant</h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
              These settings are tenant-scoped, seed automatically on first load, and stay isolated from every other tenant.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge tone="info">Tenant scoped</Badge>
            <Badge tone="neutral">{settingsId ? "Saved profile loaded" : "First-time setup"}</Badge>
          </div>
        </div>
      </section>

      {error ? <div className="rounded-2xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-200">{error}</div> : null}

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="grid gap-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">General attendance rules</h2>
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Update working days, timezone, and correction behavior.</p>
            </div>
            <Badge tone={loading ? "warning" : "success"}>{loading ? "Loading" : "Ready"}</Badge>
          </div>

          <form onSubmit={handleSubmit} className="grid gap-5">
            <div className="grid gap-4 md:grid-cols-2">
              <Input label="Duplicate detection cooldown (minutes)" type="number" min={1} value={cooldown} onChange={(event) => setCooldown(event.target.value)} helpText="Minimum 1 minute." />
              <Input label="Timezone" value={timezone} onChange={(event) => setTimezone(event.target.value)} helpText="Default: Asia/Kolkata." />
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
                <input type="checkbox" checked={allowManualCorrection} onChange={(event) => setAllowManualCorrection(event.target.checked)} />
                Allow manual correction
              </label>
              <label className="flex items-center gap-3 rounded-2xl border border-slate-200 bg-white/70 px-4 py-3 text-sm text-slate-700 shadow-sm dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200">
                <input type="checkbox" checked={requireCorrectionReason} onChange={(event) => setRequireCorrectionReason(event.target.checked)} />
                Require correction reason
              </label>
            </div>

            <div className="grid gap-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-base font-semibold text-slate-900 dark:text-white">Working days</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">Select at least one working day from Sunday to Saturday.</p>
                </div>
                <Badge tone="info">{selectedDays.length} selected</Badge>
              </div>
              <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                {dayLabels.map((day, index) => {
                  const active = selectedDays.includes(index);
                  return (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleDay(index)}
                      className={
                        active
                          ? "rounded-2xl border border-cyan-400/40 bg-cyan-500/10 px-4 py-3 text-left text-sm font-medium text-cyan-700 shadow-sm transition dark:text-cyan-200"
                          : "rounded-2xl border border-slate-200 bg-white/80 px-4 py-3 text-left text-sm font-medium text-slate-700 shadow-sm transition hover:border-cyan-300 hover:bg-cyan-500/5 dark:border-white/10 dark:bg-slate-950/60 dark:text-slate-200"
                      }
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span>{day}</span>
                        {active ? <CheckCircle2 className="h-4 w-4" /> : <span className="text-xs uppercase tracking-[0.18em] text-slate-400">Off</span>}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-dashed border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
              <span>Active working days: {workingDaySummary || "None selected"}</span>
              <span>Saved settings are tenant isolated.</span>
            </div>

            <div className="flex justify-end">
              <Button type="submit" leftIcon={saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} disabled={saving || loading}>
                {saving ? "Saving..." : "Save settings"}
              </Button>
            </div>
          </form>
        </Card>

        <Card className="grid gap-4">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Current state</h2>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">This reflects the saved attendance rule profile for the current tenant.</p>
          </div>

          <div className="grid gap-3">
            <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Cooldown</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{cooldown} min</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Timezone</div>
              <div className="mt-1 text-2xl font-semibold text-slate-900 dark:text-white">{timezone || "Asia/Kolkata"}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Working days</div>
              <div className="mt-2 flex flex-wrap gap-2">
                {selectedDays.map((day) => (
                  <Badge key={day} tone="info">
                    {dayLabels[day]}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
              <div className="text-sm text-slate-500 dark:text-slate-400">Correction policy</div>
              <div className="mt-2 grid gap-2 text-sm text-slate-700 dark:text-slate-200">
                <div>Manual correction: {allowManualCorrection ? "Enabled" : "Disabled"}</div>
                <div>Require reason: {requireCorrectionReason ? "Yes" : "No"}</div>
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-600 dark:border-white/10 dark:bg-white/5 dark:text-slate-300">
            Suggested timezone presets are provided for convenience, but any IANA timezone string can be saved.
          </div>
        </Card>
      </div>

      {toast ? (
        <div className="fixed right-4 top-4 z-50">
          <Toast
            tone={toast.tone}
            title={toast.title}
            message={toast.message}
            onClose={() => setToast(null)}
            icon={toast.tone === "success" ? <CheckCircle2 className="h-5 w-5" /> : undefined}
          />
        </div>
      ) : null}
    </div>
  );
}

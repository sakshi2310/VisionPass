import { Bell, Check, ChevronDown, KeyRound, LockKeyhole, Menu, MoonStar, Search, SunMedium } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useApp } from "@/context/AppContext";
import { initials } from "@/utils/format";

type HeaderProps = {
  onMenuClick: () => void;
};

export function Header({ onMenuClick }: HeaderProps) {
  const navigate = useNavigate();
  const { user, currentTenant, tenants, setCurrentTenantId, logout, changePassword, theme, setTheme } = useApp();
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  async function handleChangePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");
    setPasswordSuccess("");

    if (!currentPassword.trim()) {
      setPasswordError("Current password is required.");
      return;
    }
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }
    if (confirmPassword !== newPassword) {
      setPasswordError("Passwords do not match.");
      return;
    }

    try {
      setSavingPassword(true);
      await changePassword(currentPassword, newPassword);
      setPasswordSuccess("Password updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setPasswordOpen(false), 700);
    } catch (err) {
      setPasswordError(err instanceof Error ? err.message : "Unable to update password.");
    } finally {
      setSavingPassword(false);
    }
  }

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 px-4 py-4 backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/70">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" leftIcon={<Menu className="h-4 w-4" />} onClick={onMenuClick} className="md:hidden" />

        <div className="min-w-[220px] flex-1">
          <Input placeholder="Search..." leftIcon={<Search className="h-4 w-4" />} />
        </div>

        {user?.role === "SUPER_ADMIN" ? (
          <select
            value={currentTenant?.id ?? ""}
            onChange={(event) => setCurrentTenantId(event.target.value)}
            className="min-w-[180px] rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/60 dark:text-white"
          >
            {tenants.map((tenant) => (
              <option key={tenant.id} value={tenant.id} className="bg-white text-slate-900 dark:bg-slate-950 dark:text-white">
                {tenant.name}
              </option>
            ))}
          </select>
        ) : currentTenant ? (
          <Badge tone="neutral" className="px-3 py-2 text-sm font-medium">
            {currentTenant.name}
          </Badge>
        ) : null}

        <Button
          variant="ghost"
          size="sm"
          aria-label="Toggle theme"
          leftIcon={theme === "dark" ? <SunMedium className="h-4 w-4" /> : <MoonStar className="h-4 w-4" />}
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? "Light" : "Dark"}
        </Button>

        <Button variant="ghost" size="sm" aria-label="Notifications" leftIcon={<Bell className="h-4 w-4" />} />

        <details className="group relative">
          <summary className="flex cursor-pointer list-none items-center gap-3 rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm outline-none transition hover:border-slate-300 dark:border-white/10 dark:bg-slate-950/60 dark:hover:border-white/20">
            <div className="grid h-9 w-9 place-items-center rounded-2xl bg-gradient-to-br from-brand-500 to-cyan-400 text-sm font-semibold text-white">
              {user ? initials(user.name) : "VP"}
            </div>
            <div className="hidden sm:block">
              <div className="text-sm font-medium text-slate-900 dark:text-white">{user?.name ?? "Account"}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">{user?.title ?? "Vision Pass"}</div>
            </div>
            <ChevronDown className="h-4 w-4 text-slate-400 transition group-open:rotate-180" />
          </summary>

          <Card className="absolute right-0 mt-3 w-64 border-slate-200 bg-white p-3 shadow-[0_20px_60px_rgba(15,23,42,0.12)] dark:border-white/10 dark:bg-slate-950/95">
            <div className="border-b border-slate-200 pb-3 dark:border-white/10">
              <div className="text-sm font-medium text-slate-900 dark:text-white">{user?.name ?? "Account"}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">{user?.email}</div>
            </div>
            <button
              type="button"
              onClick={() => setPasswordOpen(true)}
              className="mt-3 w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-white/5"
            >
              Change password
            </button>
            <button
              type="button"
              onClick={async () => {
                const role = user?.role;
                await logout();
                navigate(role === "SUPER_ADMIN" ? "/admin/login" : "/login", { replace: true });
              }}
              className="mt-2 w-full rounded-xl px-3 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-white/5"
            >
              Logout
            </button>
          </Card>
        </details>
      </div>

      {passwordOpen ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/50 px-4">
          <Card className="w-full max-w-md border-slate-200 bg-white p-6 shadow-[0_30px_80px_rgba(15,23,42,0.22)] dark:border-white/10 dark:bg-slate-950">
            <div className="mb-5 flex items-start justify-between gap-3">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full bg-brand-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-brand-700 dark:text-brand-200">
                  <KeyRound className="h-3.5 w-3.5" />
                  Security
                </div>
                <h3 className="mt-3 text-xl font-semibold text-slate-900 dark:text-white">Change password</h3>
              </div>
              <button
                type="button"
                onClick={() => setPasswordOpen(false)}
                className="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 dark:hover:bg-white/5 dark:hover:text-white"
              >
                x
              </button>
            </div>

            <form onSubmit={handleChangePassword} className="grid gap-4">
              <Input
                label="Current password"
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
                placeholder="Enter your current password"
                leftIcon={<LockKeyhole className="h-4 w-4" />}
              />
              <Input
                label="New password"
                type="password"
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="Create a new password"
                leftIcon={<LockKeyhole className="h-4 w-4" />}
              />
              <Input
                label="Confirm new password"
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Repeat the new password"
                leftIcon={<LockKeyhole className="h-4 w-4" />}
              />

              {passwordError ? <p className="text-sm text-rose-500">{passwordError}</p> : null}
              {passwordSuccess ? <p className="text-sm text-emerald-600">{passwordSuccess}</p> : null}

              <div className="flex gap-3">
                <Button type="button" variant="secondary" className="w-full" onClick={() => setPasswordOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="w-full" disabled={savingPassword} rightIcon={<Check className="h-4 w-4" />}>
                  {savingPassword ? "Saving..." : "Save"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      ) : null}
    </header>
  );
}

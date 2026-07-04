import { type FormEvent, useState } from "react";

import { KeyRound, Mail, ShieldCheck, ServerCog, UserCog } from "lucide-react";

import { AuthInput } from "@/components/auth/AuthInput";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";

export function Settings() {
  const { user, changePassword } = useApp();
  usePageTitle("Vision Pass | Settings");
  const [passwordForm, setPasswordForm] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordError, setPasswordError] = useState("");
  const [passwordMessage, setPasswordMessage] = useState("");
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  function validatePasswordForm() {
    if (!passwordForm.currentPassword.trim()) {
      return "Current password is required.";
    }
    if (passwordForm.newPassword.length < 8) {
      return "New password must be at least 8 characters.";
    }
    if (passwordForm.confirmPassword !== passwordForm.newPassword) {
      return "New password and confirmation do not match.";
    }
    return "";
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPasswordError("");
    setPasswordMessage("");

    const validationMessage = validatePasswordForm();
    if (validationMessage) {
      setPasswordError(validationMessage);
      return;
    }

    try {
      setIsSavingPassword(true);
      await changePassword(passwordForm.currentPassword, passwordForm.newPassword);
      setPasswordMessage("Password updated successfully.");
      setPasswordForm({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error) {
      setPasswordError(error instanceof Error ? error.message : "Unable to update password.");
    } finally {
      setIsSavingPassword(false);
    }
  }

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Settings</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Profile, organization, and security settings</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Keep user details, security posture, and API integration configuration organized in one place.
        </p>
      </section>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="grid gap-4 xl:col-span-2">
          <div className="flex items-center gap-3">
            <KeyRound className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">Change password</h3>
          </div>
          <form onSubmit={handlePasswordSubmit} className="grid gap-4 md:grid-cols-2">
            <AuthInput label="Current password" type="password" autoComplete="current-password" placeholder="Enter your current password" value={passwordForm.currentPassword} onChange={(event) => setPasswordForm((current) => ({ ...current, currentPassword: event.target.value }))} error={passwordError && passwordError.includes("Current password") ? passwordError : undefined} />
            <AuthInput label="New password" type="password" autoComplete="new-password" placeholder="Create a new password" value={passwordForm.newPassword} onChange={(event) => setPasswordForm((current) => ({ ...current, newPassword: event.target.value }))} error={passwordError && passwordError.includes("New password") ? passwordError : undefined} />
            <AuthInput label="Confirm new password" type="password" autoComplete="new-password" placeholder="Repeat the new password" value={passwordForm.confirmPassword} onChange={(event) => setPasswordForm((current) => ({ ...current, confirmPassword: event.target.value }))} error={passwordError && passwordError.includes("confirmation") ? passwordError : undefined} />
            <div className="flex items-end">
              <Button type="submit" className="w-full md:w-auto" disabled={isSavingPassword}>
                {isSavingPassword ? "Updating..." : "Update password"}
              </Button>
            </div>
          </form>
          {passwordError ? <p className="text-sm text-rose-400">{passwordError}</p> : null}
          {passwordMessage ? <p className="text-sm text-emerald-400">{passwordMessage}</p> : null}
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-center gap-3">
            <UserCog className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">Profile settings</h3>
          </div>
          <Input label="Full name" defaultValue={user?.name ?? "Maya Patel"} />
          <Input label="Email" defaultValue={user?.email ?? "client@northernlights.io"} />
          <Input label="Phone" defaultValue="+1 (555) 240-9830" />
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-center gap-3">
            <Mail className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">Organization settings</h3>
          </div>
          <Input label="Organization name" defaultValue="Northern Lights HQ" />
          <Input label="Timezone" defaultValue="Asia/Calcutta" />
          <Input label="Notification email" defaultValue="security@northernlights.io" />
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">Security settings</h3>
          </div>
          <Input label="MFA policy" defaultValue="Required for all admins" />
          <Input label="Session timeout" defaultValue="30 minutes" />
          <Input label="Password rotation" defaultValue="90 days" />
        </Card>

        <Card className="grid gap-4">
          <div className="flex items-center gap-3">
            <ServerCog className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">API endpoint settings</h3>
          </div>
          <Input label="Base URL" defaultValue="http://localhost:8000/api" />
          <Input label="Webhook secret" defaultValue="masked-secret" />
          <Input label="Retry policy" defaultValue="3 attempts / exponential backoff" />
        </Card>

        <Card className="grid gap-4 xl:col-span-2">
          <div className="flex items-center gap-3">
            <KeyRound className="h-5 w-5 text-cyan-400" />
            <h3 className="text-base font-semibold">Access tokens</h3>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            {[
              { label: "Read token", value: "gm_read_masked" },
              { label: "Write token", value: "gm_write_masked" },
              { label: "Audit token", value: "gm_audit_masked" },
            ].map((item) => (
              <div key={item.label} className="rounded-2xl border border-white/10 bg-slate-950/30 p-4">
                <div className="text-sm text-slate-500 dark:text-slate-400">{item.label}</div>
                <div className="mt-2 font-mono text-sm text-white">{item.value}</div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

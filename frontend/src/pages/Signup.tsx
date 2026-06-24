import { ArrowRight, Building2, LockKeyhole, Mail, UserRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { AuthInput } from "@/components/auth/AuthInput";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { bootstrapSuperAdmin } from "@/services/auth";

type BootstrapErrors = {
  fullName?: string;
  email?: string;
  organizationName?: string;
  password?: string;
  confirmPassword?: string;
};

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function redirectForRole(role: string) {
  return role === "SUPER_ADMIN" ? "/admin/dashboard" : "/dashboard";
}

export function Signup() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    fullName: "",
    email: "",
    organizationName: "VisionPass Platform",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<BootstrapErrors>({});

  function validate() {
    const nextErrors: BootstrapErrors = {};
    if (!form.fullName.trim()) nextErrors.fullName = "Full name is required.";
    if (!form.email.trim()) nextErrors.email = "Email is required.";
    else if (!emailPattern.test(form.email)) nextErrors.email = "Enter a valid email address.";
    if (!form.organizationName.trim()) nextErrors.organizationName = "Organization name is required.";
    if (form.password.length < 8) nextErrors.password = "Use at least 8 characters.";
    if (!form.confirmPassword.trim()) nextErrors.confirmPassword = "Confirm your password.";
    else if (form.confirmPassword !== form.password) nextErrors.confirmPassword = "Passwords do not match.";
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!validate()) return;

    try {
      setIsSubmitting(true);
      const session = await bootstrapSuperAdmin(form.fullName, form.email, form.password, form.organizationName);
      navigate(redirectForRole(session.user.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to complete bootstrap.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="dark mx-auto flex min-h-[calc(100vh-3rem)] max-w-md items-center py-4">
      <Card className="w-full border-white/10 bg-slate-950/85 p-6 shadow-[0_24px_70px_rgba(2,6,23,0.42)] backdrop-blur-xl sm:p-8">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <BrandWordmark compact />
          <div className="text-sm text-slate-400">Initial platform setup for the first super admin only.</div>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <AuthInput
            label="Full name"
            autoComplete="name"
            placeholder="Full name"
            value={form.fullName}
            onChange={(event) => setForm((current) => ({ ...current, fullName: event.target.value }))}
            leftIcon={<UserRound className="h-4 w-4" />}
            error={errors.fullName}
          />
          <AuthInput
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="name@company.com"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            leftIcon={<Mail className="h-4 w-4" />}
            error={errors.email}
          />
          <AuthInput
            label="Organization name"
            autoComplete="organization"
            placeholder="VisionPass Platform"
            value={form.organizationName}
            onChange={(event) => setForm((current) => ({ ...current, organizationName: event.target.value }))}
            leftIcon={<Building2 className="h-4 w-4" />}
            error={errors.organizationName}
          />
          <AuthInput
            label="Password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a strong password"
            value={form.password}
            onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
            leftIcon={<LockKeyhole className="h-4 w-4" />}
            error={errors.password}
          />
          <AuthInput
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            placeholder="Repeat the password"
            value={form.confirmPassword}
            onChange={(event) => setForm((current) => ({ ...current, confirmPassword: event.target.value }))}
            leftIcon={<LockKeyhole className="h-4 w-4" />}
            error={errors.confirmPassword}
          />

          <p className="text-sm leading-6 text-slate-400">
            This screen is for bootstrapping the platform owner account. Client tenants should sign in with the credentials you
            create for them.
          </p>

          {error ? <p className="text-sm text-rose-400">{error}</p> : null}

          <Button type="submit" size="lg" className="w-full" rightIcon={<ArrowRight className="h-4 w-4" />} disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create super admin"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";

import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { AuthInput } from "@/components/auth/AuthInput";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { loginTenantUser } from "@/services/tenantAuth";

function redirectForRole(role: string) {
  switch (role) {
    case "SUPER_ADMIN":
      return "/admin/dashboard";
    case "TENANT_ADMIN":
      return "/tenant-admin/dashboard";
    case "SECURITY_GUARD":
      return "/user/security";
    case "RECEPTIONIST":
      return "/user/reception";
    case "ATTENDANCE_OPERATOR":
      return "/user/attendance";
    case "CAMERA_OPERATOR":
      return "/user/cameras";
    case "MANAGER":
      return "/user/security";
    case "TENANT_USER":
    default:
      return "/user/dashboard";
  }
}

export function UserLogin() {
  const navigate = useNavigate();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ email: "", password: "" });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!form.email.trim() || !form.password.trim()) {
      setError("Email and password are required.");
      return;
    }
    try {
      setIsSubmitting(true);
      const session = await loginTenantUser(form.email, form.password);
      navigate(redirectForRole(session.user.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-md items-center py-4">
      <Card className="w-full border-white/10 bg-slate-950/85 p-6 shadow-[0_24px_70px_rgba(2,6,23,0.42)] backdrop-blur-xl sm:p-8">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <BrandWordmark compact />
          <div className="space-y-1">
            <div className="text-sm font-medium text-white">VisionPass User Login</div>
            <div className="text-sm text-slate-400">Tenant users sign in with credentials issued by their tenant admin.</div>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-4">
          <AuthInput
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="name@company.com"
            value={form.email}
            onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
            leftIcon={<Mail className="h-4 w-4" />}
          />
          <div className="grid gap-2">
            <label className="text-sm font-medium text-slate-600 dark:text-slate-300">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="Enter your password"
                value={form.password}
                onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                className="h-11 w-full rounded-2xl border border-slate-200 bg-white/90 px-4 pr-12 text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100"
              />
              <button
                type="button"
                onClick={() => setShowPassword((current) => !current)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-500 transition hover:text-slate-800 dark:text-slate-400 dark:hover:text-white"
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                <span className="sr-only">Toggle password visibility</span>
              </button>
            </div>
          </div>

          {error ? <p className="text-sm text-rose-400">{error}</p> : null}

          <Button type="submit" size="lg" className="w-full" rightIcon={<ArrowRight className="h-4 w-4" />} disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign in"}
          </Button>
        </form>
      </Card>
    </div>
  );
}

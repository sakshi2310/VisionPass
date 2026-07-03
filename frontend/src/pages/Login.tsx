import { ArrowRight, LockKeyhole, Mail } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { BrandWordmark } from "@/components/brand/BrandWordmark";
import { AuthInput } from "@/components/auth/AuthInput";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { useApp } from "@/context/AppContext";

type SignInErrors = {
  email?: string;
  password?: string;
};

type LocationState = {
  message?: string;
};

function redirectForRole(role: string) {
  if (role === "SUPER_ADMIN") return "/admin/dashboard";
  if (role === "TENANT_ADMIN") return "/tenant-admin/dashboard";
  if (role === "TENANT_USER") return "/user/dashboard";
  return "/login";
}

export function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams] = useSearchParams();
  const { authReady, user, login } = useApp();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [signIn, setSignIn] = useState({ email: "", password: "" });
  const [signInErrors, setSignInErrors] = useState<SignInErrors>({});
  const workspaceName = searchParams.get("org")?.trim() || searchParams.get("tenant")?.trim() || "Vision Pass Platform";
  const stateMessage = (location.state as LocationState | null | undefined)?.message;

  useEffect(() => {
    if (!authReady || !user) return;
    navigate(redirectForRole(user.role), { replace: true });
  }, [authReady, navigate, user]);

  useEffect(() => {
    if (stateMessage) {
      setError(stateMessage);
    }
  }, [stateMessage]);

  function validateSignIn() {
    const nextErrors: SignInErrors = {};
    if (!signIn.email.trim()) {
      nextErrors.email = "Email is required.";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(signIn.email)) {
      nextErrors.email = "Enter a valid email address.";
    }
    if (!signIn.password.trim()) {
      nextErrors.password = "Password is required.";
    }
    setSignInErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  }

  async function handleSignInSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    if (!validateSignIn()) return;

    try {
      setIsSubmitting(true);
      const user = await login(signIn.email, signIn.password);
      navigate(redirectForRole(user.role), { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="dark mx-auto flex min-h-[calc(100vh-3rem)] max-w-md items-center py-4">
      <Card className="w-full border-white/10 bg-slate-950/85 p-6 shadow-[0_24px_70px_rgba(2,6,23,0.42)] backdrop-blur-xl sm:p-8">
        <div className="mb-8 flex flex-col items-center gap-4 text-center">
          <BrandWordmark compact />
          <div className="space-y-1">
            <div className="text-sm font-medium text-white">{workspaceName}</div>
            <div className="text-sm text-slate-400">Use your organization account to continue.</div>
          </div>
        </div>

        <form onSubmit={handleSignInSubmit} className="grid gap-4">
          <AuthInput
            label="Email"
            type="email"
            autoComplete="email"
            placeholder="name@company.com"
            value={signIn.email}
            onChange={(event) => setSignIn((current) => ({ ...current, email: event.target.value }))}
            leftIcon={<Mail className="h-4 w-4" />}
            error={signInErrors.email}
          />
          <AuthInput
            label="Password"
            type="password"
            autoComplete="current-password"
            placeholder="Enter your password"
            value={signIn.password}
            onChange={(event) => setSignIn((current) => ({ ...current, password: event.target.value }))}
            leftIcon={<LockKeyhole className="h-4 w-4" />}
            error={signInErrors.password}
          />

          <div className="flex items-center justify-end">
            <a
              href="mailto:support@visionpass.ai"
              className="text-sm font-medium text-cyan-300 underline decoration-cyan-300/60 underline-offset-4 hover:text-white"
            >
              Forgot password?
            </a>
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

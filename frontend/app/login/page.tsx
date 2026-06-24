"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { BrandMark } from "@/components/brand-mark";

type LoginResponse = {
  token: {
    access_token: string;
    token_type: string;
  };
  user: {
    id: string;
    email: string;
    full_name: string;
    role: string;
    tenant_id: string | null;
    is_active: boolean;
    created_at: string;
  };
};

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as { detail?: string } | null;
        throw new Error(payload?.detail ?? "Login failed");
      }

      const data = (await response.json()) as LoginResponse;
      localStorage.setItem("visionpass_token", data.token.access_token);
      localStorage.setItem("visionpass_user", JSON.stringify(data.user));
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell
      title="Sign in"
      subtitle="Access the tenant dashboard, module controls, and live operational views."
    >
      <div className="form-card">
        <div className="form-card-header">
          <BrandMark />
          <div>
            <div className="form-card-title">Welcome back</div>
            <div className="form-card-subtitle">Use your company account to continue.</div>
          </div>
        </div>
        <form className="stack" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input id="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <div className="error">{error}</div>
          <button className="button" type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Login"}
          </button>
        </form>
      </div>
    </AppShell>
  );
}

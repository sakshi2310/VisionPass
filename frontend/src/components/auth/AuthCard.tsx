import type { ReactNode } from "react";

import { BrandMark } from "@/components/brand/BrandMark";
import { Card } from "@/components/ui/Card";
import { cn } from "@/utils/cn";

export type AuthMode = "signIn" | "createAccount";

type AuthCardProps = {
  mode: AuthMode;
  onModeChange: (mode: AuthMode) => void;
  title: string;
  subtitle: string;
  children: ReactNode;
};

const tabStyles = {
  active: "bg-slate-900 text-white shadow-sm dark:bg-white dark:text-slate-900",
  inactive: "text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white",
};

export function AuthCard({ mode, onModeChange, title, subtitle, children }: AuthCardProps) {
  return (
    <div className="mx-auto grid min-h-[calc(100vh-3rem)] max-w-6xl gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <aside className="relative overflow-hidden rounded-[2rem] border border-white/30 bg-gradient-to-br from-indigo-600 via-blue-600 to-cyan-500 p-8 text-white shadow-[0_24px_70px_rgba(37,99,235,0.22)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(255,255,255,0.22),_transparent_26%),radial-gradient(circle_at_bottom_left,_rgba(255,255,255,0.14),_transparent_28%)]" />
        <div className="relative flex h-full flex-col justify-between gap-10">
          <div className="space-y-8">
            <div className="flex items-center gap-3">
              <BrandMark className="h-12 w-12" />
              <div>
                <div className="text-lg font-semibold tracking-tight">VisionPass AI</div>
                <div className="text-sm text-white/80">Gate and security operations, simplified</div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-white/90">
                Multi-tenant access
              </div>
              <h1 className="max-w-sm text-4xl font-semibold tracking-tight">
                Clean access for every tenant, team, and gate.
              </h1>
              <p className="max-w-sm text-sm leading-6 text-white/82">
                A focused auth experience for platform admins and client workspaces.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 text-sm">
            {["Secure login", "Invite only", "Role aware"].map((item) => (
              <div key={item} className="rounded-2xl border border-white/15 bg-white/10 px-3 py-3 text-white/90 backdrop-blur">
                {item}
              </div>
            ))}
          </div>
        </div>
      </aside>

      <section className="flex items-center">
        <Card className="w-full border-slate-200 bg-white/95 p-6 shadow-[0_16px_40px_rgba(15,23,42,0.08)] backdrop-blur-xl dark:border-white/10 dark:bg-slate-950/80 lg:p-8">
          <div className="mb-6 flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.24em] text-brand-600">
                {mode === "signIn" ? "Sign in" : "Create account"}
              </div>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-400">{subtitle}</p>
            </div>
          </div>

          <div className="mb-6 inline-flex rounded-2xl bg-slate-100 p-1 dark:bg-white/5">
            {[
              { key: "signIn" as const, label: "Sign in" },
              { key: "createAccount" as const, label: "Create account" },
            ].map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => onModeChange(tab.key)}
                className={cn(
                  "rounded-xl px-4 py-2 text-sm font-medium transition",
                  mode === tab.key ? tabStyles.active : tabStyles.inactive,
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {children}
        </Card>
      </section>
    </div>
  );
}

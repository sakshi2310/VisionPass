import { Building2, Clock3, ShieldCheck, UserRound } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useApp } from "@/context/AppContext";
import { usePageTitle } from "@/hooks/usePageTitle";
import { getUserWorkspaceDashboard, type UserWorkspaceDashboard } from "@/services/userWorkspace";

export function TenantUserProfile() {
  const { user, currentTenant } = useApp();
  const [dashboard, setDashboard] = useState<UserWorkspaceDashboard | null>(null);

  usePageTitle("VisionPass AI | Profile");

  useEffect(() => {
    let cancelled = false;
    void getUserWorkspaceDashboard()
      .then((data) => {
        if (!cancelled) setDashboard(data);
      })
      .catch(() => {
        // Profile still renders from app context.
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const profile = dashboard?.profile;
  const profileStatus = profile?.status ?? (user?.isActive ? "active" : "inactive");

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Profile</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">My profile</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Your profile is visible only for the logged-in member and always stays within the current tenant scope.
        </p>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400"><UserRound className="h-5 w-5" /></div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Name</div>
              <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">{profile?.full_name ?? user?.name ?? "-"}</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400"><ShieldCheck className="h-5 w-5" /></div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Role</div>
              <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">{profile?.role ?? user?.role ?? "user"}</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400"><Building2 className="h-5 w-5" /></div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Tenant</div>
              <div className="mt-1 text-lg font-semibold text-slate-900 dark:text-white">{currentTenant?.name ?? "-"}</div>
            </div>
          </div>
        </Card>
        <Card className="p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-2xl border border-cyan-500/20 bg-cyan-500/10 p-3 text-cyan-400"><Clock3 className="h-5 w-5" /></div>
            <div>
              <div className="text-sm text-slate-500 dark:text-slate-400">Status</div>
              <div className="mt-1"><Badge tone={profileStatus === "active" ? "success" : profileStatus === "suspended" ? "warning" : "danger"}>{profileStatus}</Badge></div>
            </div>
          </div>
        </Card>
      </div>

      <Card className="grid gap-3 p-5">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Account details</h2>
        <div className="grid gap-3 text-sm text-slate-600 dark:text-slate-300 md:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">Email: {profile?.email ?? user?.email ?? "-"}</div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">Member ID: {profile?.id ?? user?.id ?? "-"}</div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">Tenant ID: {profile?.tenant_id ?? user?.tenantId ?? "-"}</div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-white/10 dark:bg-slate-950/30">Last login: {profile?.last_login_at ?? "-"}</div>
        </div>
      </Card>
    </div>
  );
}

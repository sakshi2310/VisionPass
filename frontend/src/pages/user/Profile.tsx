import { Building2, Clock3, ScanFace, UserRound } from "lucide-react";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { usePageTitle } from "@/hooks/usePageTitle";
import { meApi, type MeProfile } from "@/services/me";

export function TenantUserProfile() {
  const [profile, setProfile] = useState<MeProfile | null>(null);
  const [error, setError] = useState("");
  usePageTitle("Vision Pass | My Profile");

  useEffect(() => {
    void meApi.profile().then(setProfile).catch((caught) => setError(caught instanceof Error ? caught.message : "Profile could not be loaded."));
  }, []);

  if (error) return <EmptyState title="Profile unavailable" description={error} />;

  const cards = [
    { label: "Department", value: profile?.department ?? "Not assigned", icon: Building2 },
    { label: "Designation", value: profile?.designation ?? "Not assigned", icon: UserRound },
    { label: "Current shift", value: profile?.shift?.name ?? "Not assigned", icon: Clock3 },
    { label: "Face enrollment", value: profile?.face_enrollment_status ?? "Loading…", icon: ScanFace },
  ];

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">My profile</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">{profile?.full_name ?? "Loading profile…"}</h1>
        <p className="mt-2 text-sm text-slate-400">Personal and employment details linked to your account.</p>
      </section>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ label, value, icon: Icon }) => (
          <Card key={label}>
            <Icon className="h-5 w-5 text-cyan-500" />
            <p className="mt-4 text-sm text-slate-500">{label}</p>
            <p className="mt-1 font-semibold text-slate-900 dark:text-white">{value}</p>
          </Card>
        ))}
      </section>

      <Card>
        <div className="flex items-center justify-between"><h2 className="text-xl font-semibold text-slate-900 dark:text-white">Personal details</h2><Badge tone={profile?.status === "active" ? "success" : "warning"}>{profile?.status ?? "loading"}</Badge></div>
        <div className="mt-5 grid gap-3 md:grid-cols-2">
          {[
            ["Email", profile?.email],
            ["Phone", profile?.phone],
            ["Employee code", profile?.employee_code],
            ["Employee type", profile?.employee_type],
            ["Joining date", profile?.joining_date],
            ["Face images", profile ? String(profile.face_count) : undefined],
          ].map(([label, value]) => (
            <div key={label} className="rounded-2xl border border-slate-200 p-4 dark:border-white/10">
              <p className="text-xs uppercase tracking-wide text-slate-500">{label}</p>
              <p className="mt-2 text-sm font-medium text-slate-900 dark:text-white">{value ?? "—"}</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

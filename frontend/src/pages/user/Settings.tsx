import { Moon, ShieldCheck } from "lucide-react";

import { Card } from "@/components/ui/Card";
import { usePageTitle } from "@/hooks/usePageTitle";

export function TenantUserSettings() {
  usePageTitle("Vision Pass | My Settings");
  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Settings</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Personal settings</h1>
        <p className="mt-2 text-sm text-slate-400">Account-level preferences only. Organization configuration remains administrator-controlled.</p>
      </section>
      <div className="grid gap-4 md:grid-cols-2">
        <Card><Moon className="h-5 w-5 text-cyan-500" /><h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Appearance</h2><p className="mt-2 text-sm text-slate-500">Use the theme control in the header to switch between light and dark mode.</p></Card>
        <Card><ShieldCheck className="h-5 w-5 text-cyan-500" /><h2 className="mt-4 font-semibold text-slate-900 dark:text-white">Privacy scope</h2><p className="mt-2 text-sm text-slate-500">Your workspace only retrieves your own profile, attendance, shift, and notifications.</p></Card>
      </div>
    </div>
  );
}

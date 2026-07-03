import { Card } from "@/components/ui/Card";
import { usePageTitle } from "@/hooks/usePageTitle";

export function AdminAnalytics() {
  usePageTitle("Vision Pass | Analytics");

  return (
    <div className="grid gap-6">
      <section className="surface-strong p-7">
        <p className="text-sm uppercase tracking-[0.24em] text-cyan-300">Platform analytics</p>
        <h1 className="mt-2 text-3xl font-semibold text-white">Cross-tenant analytics</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-400">
          Live platform analytics will appear here after the metrics API is implemented.
        </p>
      </section>

      <Card className="grid gap-4">
        <h3 className="text-base font-semibold">Analytics pending</h3>
        <p className="text-sm leading-6 text-slate-500 dark:text-slate-400">
          TODO: Connect this page to real tenant feature-adoption and system-health metrics. Mock percentages have
          been removed so the dashboard does not present invented operational data.
        </p>
      </Card>
    </div>
  );
}

import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

type DataTableProps = {
  title?: string;
  subtitle?: string;
  headers: string[];
  children: ReactNode;
  emptyState?: ReactNode;
};

export function DataTable({ title, subtitle, headers, children, emptyState }: DataTableProps) {
  return (
    <Card className="overflow-hidden p-0">
      {(title || subtitle) && (
        <div className="border-b border-slate-200 px-5 py-4 dark:border-white/10">
          {title ? <h3 className="text-base font-semibold">{title}</h3> : null}
          {subtitle ? <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{subtitle}</p> : null}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 dark:divide-white/10">
          <thead className="bg-slate-50 text-left text-xs uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-950/30 dark:text-slate-400">
            <tr>
              {headers.map((header) => (
                <th key={header} className="px-5 py-4 font-medium">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-white/10">{children}</tbody>
        </table>
      </div>
      {emptyState}
    </Card>
  );
}

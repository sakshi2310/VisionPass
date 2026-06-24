import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

type ChartCardProps = {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
};

export function ChartCard({ title, description, children, className }: ChartCardProps) {
  return (
    <Card className={className}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold">{title}</h3>
          {description ? <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p> : null}
        </div>
      </div>
      {children}
    </Card>
  );
}

import type { ReactNode } from "react";

import { Card } from "@/components/ui/Card";

type EmptyStateProps = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <Card className="grid place-items-center gap-3 py-12 text-center">
      <div className="max-w-sm">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-500 dark:text-slate-400">{description}</p>
      </div>
      {action}
    </Card>
  );
}

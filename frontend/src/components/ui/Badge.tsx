import type { HTMLAttributes } from "react";

import { cn } from "@/utils/cn";
import type { Severity } from "@/types";

type BadgeTone = "neutral" | "success" | "warning" | "danger" | "info" | Severity;

const toneClasses: Record<BadgeTone, string> = {
  neutral: "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-500/10 dark:text-slate-200 dark:ring-slate-500/20",
  success: "bg-emerald-500/10 text-emerald-600 ring-emerald-500/20",
  warning: "bg-amber-500/10 text-amber-600 ring-amber-500/20",
  danger: "bg-rose-500/10 text-rose-600 ring-rose-500/20",
  info: "bg-cyan-500/10 text-cyan-600 ring-cyan-500/20",
  low: "bg-emerald-500/10 text-emerald-600 ring-emerald-500/20",
  medium: "bg-amber-500/10 text-amber-600 ring-amber-500/20",
  high: "bg-orange-500/10 text-orange-600 ring-orange-500/20",
  critical: "bg-rose-500/10 text-rose-600 ring-rose-500/20",
};

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: BadgeTone;
};

export function Badge({ className, tone = "neutral", children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset",
        toneClasses[tone],
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}

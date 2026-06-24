import type { InputHTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  label?: string;
  helpText?: string;
  leftIcon?: ReactNode;
};

export function Input({ className, label, helpText, leftIcon, ...props }: InputProps) {
  return (
    <label className="grid gap-2">
      {label ? <span className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</span> : null}
      <span className="relative">
        {leftIcon ? <span className="pointer-events-none absolute inset-y-0 left-3 flex items-center text-slate-400">{leftIcon}</span> : null}
        <input
          className={cn(
            "h-11 w-full rounded-2xl border border-slate-200 bg-white/90 px-4 text-slate-900 shadow-sm outline-none transition focus:border-brand-400 focus:ring-2 focus:ring-brand-400/20 dark:border-white/10 dark:bg-slate-950/70 dark:text-slate-100",
            leftIcon ? "pl-10" : "",
            className,
          )}
          {...props}
        />
      </span>
      {helpText ? <span className="text-xs text-slate-500 dark:text-slate-400">{helpText}</span> : null}
    </label>
  );
}

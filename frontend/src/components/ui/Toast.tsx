import { X } from "lucide-react";
import type { ReactNode } from "react";

import { cn } from "@/utils/cn";

export type ToastTone = "success" | "error" | "info";

type ToastProps = {
  tone?: ToastTone;
  title: string;
  message: string;
  onClose?: () => void;
  icon?: ReactNode;
};

const toneClasses: Record<ToastTone, string> = {
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-50",
  error: "border-rose-500/30 bg-rose-500/10 text-rose-50",
  info: "border-cyan-500/30 bg-cyan-500/10 text-cyan-50",
};

export function Toast({ tone = "info", title, message, onClose, icon }: ToastProps) {
  return (
    <div className={cn("pointer-events-auto w-full max-w-sm rounded-3xl border px-4 py-3 shadow-[0_24px_60px_rgba(15,23,42,0.22)] backdrop-blur", toneClasses[tone])}>
      <div className="flex items-start gap-3">
        {icon ? <div className="mt-0.5">{icon}</div> : null}
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold">{title}</div>
          <div className="mt-1 text-sm/6 opacity-90">{message}</div>
        </div>
        {onClose ? (
          <button type="button" onClick={onClose} className="rounded-full p-1 text-current/80 transition hover:bg-white/10 hover:text-white">
            <span className="sr-only">Dismiss</span>
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>
    </div>
  );
}

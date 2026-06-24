import { type ReactNode, useEffect } from "react";
import { createPortal } from "react-dom";
import { X } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { cn } from "@/utils/cn";

type ModalProps = {
  open: boolean;
  title: string;
  description?: string;
  onClose: () => void;
  children: ReactNode;
  className?: string;
  footer?: ReactNode;
};

export function Modal({ open, title, description, onClose, children, className, footer }: ModalProps) {
  useEffect(() => {
    if (!open) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
    };

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose, open]);

  if (!open || typeof document === "undefined") return null;

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6 backdrop-blur-md">
      <button type="button" aria-label="Close modal" className="absolute inset-0 cursor-default" onClick={onClose} />
      <Card className={cn("relative z-10 w-full max-w-4xl border-slate-200/80 bg-white p-0 shadow-[0_35px_100px_rgba(15,23,42,0.3)] animate-modal-in dark:border-white/10 dark:bg-slate-950", className)}>
        <div className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4 dark:border-white/10">
          <div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white">{title}</h3>
            {description ? <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{description}</p> : null}
          </div>
          <Button variant="ghost" size="sm" leftIcon={<X className="h-4 w-4" />} onClick={onClose} />
        </div>
        <div className="max-h-[75vh] overflow-y-auto px-5 py-5">{children}</div>
        {footer ? <div className="border-t border-slate-200 px-5 py-4 dark:border-white/10">{footer}</div> : null}
      </Card>
    </div>,
    document.body,
  );
}

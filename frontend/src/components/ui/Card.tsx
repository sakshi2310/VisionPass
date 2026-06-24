import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/utils/cn";

type CardProps = HTMLAttributes<HTMLDivElement> & {
  children: ReactNode;
};

export function Card({ className, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-slate-200 bg-white/80 p-5 shadow-soft backdrop-blur dark:border-white/10 dark:bg-slate-950/75",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

import type { ComponentProps, ReactNode } from "react";

import { Input } from "@/components/ui/Input";

type AuthInputProps = ComponentProps<typeof Input> & {
  error?: string;
  hint?: string;
  leftIcon?: ReactNode;
};

export function AuthInput({ error, hint, ...props }: AuthInputProps) {
  return (
    <div className="grid gap-2">
      <Input {...props} />
      {error ? <p className="text-xs text-rose-500">{error}</p> : null}
      {!error && hint ? <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p> : null}
    </div>
  );
}

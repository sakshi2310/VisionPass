import { cn } from "@/utils/cn";

type ToggleProps = {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
};

export function Toggle({ checked, onChange, label }: ToggleProps) {
  return (
    <button
      type="button"
      aria-pressed={checked}
      onClick={() => onChange(!checked)}
      className={cn(
        "inline-flex items-center gap-3 rounded-full border border-white/10 px-3 py-2 text-sm transition",
        checked ? "bg-emerald-500/15 text-emerald-500" : "bg-slate-950/40 text-slate-400",
      )}
    >
      <span
        className={cn(
          "relative h-6 w-11 rounded-full transition",
          checked ? "bg-emerald-500" : "bg-slate-700",
        )}
      >
        <span
          className={cn(
            "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform",
            checked ? "translate-x-5" : "translate-x-0.5",
          )}
        />
      </span>
      {label ? <span>{label}</span> : null}
    </button>
  );
}

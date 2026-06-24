import { Badge } from "@/components/ui/Badge";
import { Toggle } from "@/components/ui/Toggle";
import { moduleDefinitions } from "@/constants/modules";
import type { ModuleKey } from "@/types";

type ModuleToggleProps = {
  moduleKey: ModuleKey;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
};

export function ModuleToggle({ moduleKey, enabled, onChange }: ModuleToggleProps) {
  const module = moduleDefinitions.find((item) => item.key === moduleKey);

  if (!module) return null;

  return (
    <div className="flex items-start justify-between gap-4 rounded-2xl border border-white/10 bg-slate-950/30 p-4">
      <div>
        <div className="flex items-center gap-2">
          <h4 className="font-medium">{module.label}</h4>
          <Badge tone={enabled ? "success" : "neutral"}>{enabled ? "enabled" : "disabled"}</Badge>
        </div>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{module.description}</p>
      </div>
      <Toggle checked={enabled} onChange={onChange} />
    </div>
  );
}

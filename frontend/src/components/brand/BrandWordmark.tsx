import { BrandMark } from "@/components/brand/BrandMark";

type BrandWordmarkProps = {
  compact?: boolean;
};

export function BrandWordmark({ compact }: BrandWordmarkProps) {
  return (
    <div className="flex items-center gap-3">
      <BrandMark className={compact ? "h-10 w-10" : "h-12 w-12"} />
      <div>
        <div className={compact ? "text-base font-semibold tracking-tight text-slate-900 dark:text-white" : "text-lg font-semibold tracking-tight text-slate-900 dark:text-white"}>
          Vision Pass
        </div>
        {!compact ? (
          <div className="text-sm text-slate-500 dark:text-slate-400">Secure visitor and access intelligence</div>
        ) : null}
      </div>
    </div>
  );
}

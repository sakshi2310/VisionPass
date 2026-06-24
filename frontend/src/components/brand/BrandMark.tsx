import { useId } from "react";

type BrandMarkProps = {
  className?: string;
};

export function BrandMark({ className = "h-12 w-12" }: BrandMarkProps) {
  const gradientId = useId().replace(/:/g, "");

  return (
    <div
      className={`grid place-items-center rounded-[1.15rem] bg-white/80 shadow-[0_18px_45px_rgba(37,99,235,0.18)] ring-1 ring-slate-200/80 backdrop-blur dark:bg-slate-950/70 dark:ring-white/10 ${className}`}
      aria-hidden="true"
    >
      <svg viewBox="0 0 120 120" className="h-[74%] w-[74%]" role="presentation">
        <defs>
          <linearGradient id={gradientId} x1="20" y1="18" x2="104" y2="104" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="var(--visionpass-logo-start)" />
            <stop offset="50%" stopColor="var(--visionpass-logo-mid)" />
            <stop offset="100%" stopColor="var(--visionpass-logo-end)" />
          </linearGradient>
          <linearGradient id={`${gradientId}-eye`} x1="38" y1="38" x2="82" y2="82" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#eef2ff" />
          </linearGradient>
        </defs>

        <path
          d="M19 30h21l19 40 21-40h21L60 95 19 30Z"
          fill={`url(#${gradientId})`}
        />
        <path
          d="M72 26h16c18 0 30 11 30 28s-12 28-30 28H76l-10-12h20c9 0 15-6 15-16s-6-16-15-16H70l2-12Z"
          fill={`url(#${gradientId})`}
          opacity="0.95"
        />
        <path
          d="M28 66c8-15 21-24 34-24 12 0 23 6 33 18-10 12-21 18-33 18-14 0-26-7-34-12Z"
          fill={`url(#${gradientId}-eye)`}
          opacity="0.98"
        />
        <circle cx="61" cy="64" r="19" fill="#ffffff" />
        <circle cx="61" cy="64" r="15" fill="var(--visionpass-logo-pupil)" />
        <circle cx="66" cy="58" r="4.5" fill="#ffffff" />
        <path
          d="M43 56c5-8 11-13 19-16"
          fill="none"
          stroke="rgba(255,255,255,0.9)"
          strokeLinecap="round"
          strokeWidth="5"
        />
      </svg>
    </div>
  );
}

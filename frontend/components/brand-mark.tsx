export function BrandMark() {
  return (
    <div className="brand-mark" aria-hidden="true">
      <svg viewBox="0 0 40 40" role="presentation">
        <rect x="6" y="6" width="28" height="28" rx="10" className="brand-mark-frame" />
        <path
          d="M12 22.5V17.8L20 13l8 4.8v4.7L20 27l-8-4.5Z"
          className="brand-mark-shape"
        />
        <circle cx="20" cy="20" r="3.2" className="brand-mark-core" />
      </svg>
    </div>
  );
}


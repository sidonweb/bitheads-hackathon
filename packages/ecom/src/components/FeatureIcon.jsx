const ICONS = {
  noise: (
    <path
      d="M12 3v18M8 7v10M16 7v10M4 10v4M20 10v4"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
    />
  ),
  battery: (
    <>
      <rect x="4" y="7" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.8" fill="none" />
      <path d="M20 10v4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </>
  ),
  bluetooth: (
    <path
      d="M7 7l10 10-5 3V4l5 3L7 17"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
      fill="none"
    />
  ),
  comfort: (
    <path
      d="M12 21s-6-4.5-6-10a6 6 0 1112 0c0 5.5-6 10-6 10z"
      stroke="currentColor"
      strokeWidth="1.8"
      fill="none"
    />
  ),
  speed: (
    <path
      d="M13 2L4 14h7l-1 8 9-12h-7l1-8z"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinejoin="round"
      fill="none"
    />
  ),
  shield: (
    <path
      d="M12 2l8 4v6c0 5-3.5 9-8 10-4.5-1-8-5-8-10V6l8-4z"
      stroke="currentColor"
      strokeWidth="1.8"
      fill="none"
    />
  ),
  plug: (
    <>
      <path d="M9 7v4M15 7v4M12 7v10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      <path d="M7 11h10v4H7z" stroke="currentColor" strokeWidth="1.8" fill="none" />
    </>
  ),
  star: (
    <path
      d="M12 3l2.4 5.8H21l-4.8 3.5 1.8 5.7L12 15.8 6 17.9l1.8-5.7L3 8.8h6.6L12 3z"
      stroke="currentColor"
      strokeWidth="1.5"
      fill="none"
    />
  ),
};

export default function FeatureIcon({ name }) {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      {ICONS[name] || ICONS.star}
    </svg>
  );
}

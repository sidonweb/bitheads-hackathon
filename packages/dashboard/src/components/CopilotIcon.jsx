export default function CopilotIcon({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden>
      <defs>
        <linearGradient id="copilot-grad" x1="4" y1="4" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#0078D4" />
          <stop offset=".45" stopColor="#8661C5" />
          <stop offset="1" stopColor="#00A2ED" />
        </linearGradient>
      </defs>
      <path
        d="M16 3c1.2 3.8 3.8 6.4 7.6 7.6-3.8 1.2-6.4 3.8-7.6 7.6-1.2-3.8-3.8-6.4-7.6-7.6C12.2 9.4 14.8 6.8 16 3Z"
        fill="url(#copilot-grad)"
      />
      <path
        d="M24 14c.7 2.2 2.2 3.7 4.4 4.4-2.2.7-3.7 2.2-4.4 4.4-.7-2.2-2.2-3.7-4.4-4.4 2.2-.7 3.7-2.2 4.4-4.4Z"
        fill="url(#copilot-grad)"
        opacity=".85"
      />
    </svg>
  );
}

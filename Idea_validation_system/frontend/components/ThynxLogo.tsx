/** components/ThynxLogo.tsx — Inline SVG logo matching the Thynx brand */
import React from "react";

interface Props {
  size?: "sm" | "md" | "lg";
  variant?: "full" | "icon";
}

const sizes = {
  sm: { width: 120, height: 36 },
  md: { width: 180, height: 54 },
  lg: { width: 260, height: 78 },
};

export default function ThynxLogo({ size = "md", variant = "full" }: Props) {
  const { width, height } = sizes[size];

  if (variant === "icon") {
    return (
      <svg width={40} height={40} viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect width="40" height="40" rx="8" fill="#161B27" />
        {/* T shape */}
        <rect x="6" y="8" width="12" height="3.5" rx="1.5" fill="#E6EDF3" />
        <rect x="10.5" y="11.5" width="3" height="14" rx="1.5" fill="#E6EDF3" />
        {/* Diagonal slash */}
        <line x1="20" y1="28" x2="34" y2="10" stroke="#4361EE" strokeWidth="3.5" strokeLinecap="round" />
        {/* Right bar */}
        <rect x="33" y="8" width="3" height="20" rx="1.5" fill="#4361EE" />
      </svg>
    );
  }

  return (
    <svg
      width={width}
      height={height}
      viewBox="0 0 260 78"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="ThynxAI — Beyond Intelligence"
    >
      {/* ── THYNX letters ────────────────────────────────── */}

      {/* T */}
      <rect x="0"  y="8"  width="34" height="7"  rx="3.5" fill="#E6EDF3" />
      <rect x="13.5" y="14" width="7" height="36"  rx="3.5" fill="#E6EDF3" />

      {/* H */}
      <rect x="42"  y="8"  width="7" height="42" rx="3.5" fill="#E6EDF3" />
      <rect x="42"  y="24" width="24" height="7" rx="3.5" fill="#E6EDF3" />
      <rect x="59"  y="8"  width="7" height="42" rx="3.5" fill="#E6EDF3" />

      {/* Y */}
      <rect x="73"  y="8"  width="7"  height="22" rx="3.5" transform="rotate(20 73 8)"  fill="#E6EDF3" />
      <rect x="93"  y="8"  width="7"  height="22" rx="3.5" transform="rotate(-20 100 8)" fill="#E6EDF3" />
      <rect x="84"  y="28" width="7"  height="22" rx="3.5" fill="#E6EDF3" />

      {/* N */}
      <rect x="110" y="8"  width="7" height="42" rx="3.5" fill="#E6EDF3" />
      <rect x="127" y="8"  width="7" height="42" rx="3.5" fill="#E6EDF3" />
      <line x1="117" y1="10" x2="134" y2="48" stroke="#E6EDF3" strokeWidth="7" strokeLinecap="round" />

      {/* X — diagonal slash (blue) + right stroke */}
      <line x1="148" y1="50" x2="174" y2="8"  stroke="#4361EE" strokeWidth="7.5" strokeLinecap="round" />
      <line x1="148" y1="8"  x2="174" y2="50" stroke="#E6EDF3" strokeWidth="7.5" strokeLinecap="round" />

      {/* AI letters */}
      {/* A */}
      <line x1="184" y1="50" x2="192" y2="8"  stroke="#E6EDF3" strokeWidth="6" strokeLinecap="round" />
      <line x1="192" y1="8"  x2="200" y2="50" stroke="#E6EDF3" strokeWidth="6" strokeLinecap="round" />
      <rect x="185" y="30" width="14" height="5.5" rx="2.75" fill="#E6EDF3" />

      {/* i */}
      <rect x="210" y="8"  width="6" height="6"  rx="3"   fill="#4361EE" />
      <rect x="207" y="18" width="12" height="32" rx="3.5" fill="#4361EE" />

      {/* BEYOND INTELLIGENCE */}
      <text
        x="0"
        y="74"
        fontSize="9.5"
        fontWeight="600"
        letterSpacing="4"
        fill="#8B949E"
        fontFamily="Inter, sans-serif"
        textAnchor="start"
      >
        BEYOND INTELLIGENCE
      </text>
    </svg>
  );
}

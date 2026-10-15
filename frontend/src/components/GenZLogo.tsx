import React from "react"

interface GenZLogoProps {
  size?: number
  className?: string
}

export const GenZLogo: React.FC<GenZLogoProps> = ({
  size = 32,
  className = "",
}) => {
  return (
    <span
      className={`genz-logo-wrapper ${className}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        verticalAlign: "middle",
        lineHeight: 0,
        flexShrink: 0,
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 44 44"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="genz-logo-svg"
        aria-hidden="true"
      >
        <defs>
          <linearGradient id="gzBgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#090d16" />
            <stop offset="45%" stopColor="#1e1b4b" />
            <stop offset="100%" stopColor="#4338ca" />
          </linearGradient>
          <linearGradient id="gzGoldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fef08a" />
            <stop offset="45%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#b45309" />
          </linearGradient>
          <linearGradient id="gzNeonGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="100%" stopColor="#c7d2fe" />
          </linearGradient>
          <filter id="gzGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor="#6366f1" floodOpacity="0.45" />
          </filter>
        </defs>

        {/* Outer Elegant Squircle with Luxury Indigo Gradient & Gold Trim */}
        <rect
          x="1.5"
          y="1.5"
          width="41"
          height="41"
          rx="11"
          fill="url(#gzBgGrad)"
          stroke="url(#gzGoldGrad)"
          strokeWidth="1.6"
          filter="url(#gzGlow)"
        />

        {/* Inner Subtle Inset Frame */}
        <rect
          x="3.5"
          y="3.5"
          width="37"
          height="37"
          rx="9"
          fill="none"
          stroke="rgba(255, 255, 255, 0.12)"
          strokeWidth="1"
        />

        {/* Minimalist Shopping Bag Handles */}
        <path
          d="M17 14 C17 9.5, 27 9.5, 27 14"
          fill="none"
          stroke="url(#gzGoldGrad)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />

        {/* Stylized Modern Letter G */}
        <path
          d="M20 18 H15.5 C13.5 18 12 19.5 12 21.5 V26.5 C12 28.5 13.5 30 15.5 30 H21 C22.8 30 24 28.8 24 27 V24 H18"
          fill="none"
          stroke="url(#gzNeonGrad)"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Stylized Dynamic Letter Z (Interlocking with Gold Sheen) */}
        <path
          d="M23 18.5 H31.5 L24 29 H32.5"
          fill="none"
          stroke="url(#gzGoldGrad)"
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Top-Right 4-point Diamond Star Sparkle */}
        <path
          d="M34 6 L35.2 9.2 L38.5 10.5 L35.2 11.8 L34 15 L32.8 11.8 L29.5 10.5 L32.8 9.2 Z"
          fill="url(#gzGoldGrad)"
        />
        <circle cx="34" cy="10.5" r="1.1" fill="#ffffff" />
      </svg>
    </span>
  )
}

export default GenZLogo

import Link from 'next/link';

/** GOLAZO mark — a speeding ball trailing a golden streak, plus wordmark. */
export function BallMark({ size = 36 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none"
         xmlns="http://www.w3.org/2000/svg" aria-hidden>
      <defs>
        <linearGradient id="g-streak" x1="0" y1="0" x2="48" y2="48">
          <stop offset="0" stopColor="#f5c518" />
          <stop offset="1" stopColor="#16c784" />
        </linearGradient>
        <radialGradient id="g-ball" cx="35%" cy="30%" r="80%">
          <stop offset="0" stopColor="#ffffff" />
          <stop offset="1" stopColor="#bfeede" />
        </radialGradient>
      </defs>
      {/* speed streaks */}
      <path d="M2 30 H16" stroke="url(#g-streak)" strokeWidth="3" strokeLinecap="round" opacity="0.5" />
      <path d="M4 22 H14" stroke="url(#g-streak)" strokeWidth="3" strokeLinecap="round" opacity="0.8" />
      <path d="M6 14 H18" stroke="url(#g-streak)" strokeWidth="3" strokeLinecap="round" opacity="0.4" />
      {/* ball */}
      <circle cx="31" cy="22" r="14" fill="url(#g-ball)" stroke="#0a2c22" strokeWidth="1.5" />
      <path d="M31 14 l4.7 3.4 -1.8 5.5 -5.8 0 -1.8 -5.5 z" fill="#0a2c22" />
      <path d="M31 14 v-3 M37.8 19 l3-1 M24.2 19 l-3-1 M27 28 l-2 2.6 M35 28 l2 2.6"
            stroke="#0a2c22" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

export function Logo({ size = 36 }: { size?: number }) {
  return (
    <Link href="/" className="flex items-center gap-2 group">
      <BallMark size={size} />
      <span className="leading-none">
        <span className="block font-display text-xl tracking-tight text-ink group-hover:text-grass-400 transition">
          GOLAZO
        </span>
        <span className="block text-[10px] font-semibold tracking-[0.35em] text-gold-400">
          WORLD CUP 2026
        </span>
      </span>
    </Link>
  );
}

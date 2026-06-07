'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Logo } from './Logo';
import { api, fmtCoins, type Profile } from '@/lib/api';
import { clearSession, useToken } from '@/lib/auth';

const LINKS = [
  ['/matches', 'Matches'],
  ['/teams', 'Teams'],
  ['/simulator', 'Simulator'],
  ['/leaderboard', 'Leaderboard'],
  ['/science', 'The Science'],
];

export function NavBar() {
  const { token, ready } = useToken();
  const router = useRouter();
  const path = usePathname();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!token) { setProfile(null); return; }
    api.get<Profile>('/me', token).then(setProfile).catch(() => setProfile(null));
  }, [token, path]);

  return (
    <nav className="sticky top-0 z-30 border-b border-white/10 bg-pitch-900/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
        <Logo size={34} />
        <div className="hidden items-center gap-1 md:flex">
          {LINKS.map(([href, label]) => (
            <Link key={href} href={href}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition
                ${path.startsWith(href) ? 'text-grass-400' : 'text-ink/80 hover:text-ink'}`}>
              {label}
            </Link>
          ))}
          {profile?.is_admin && (
            <Link href="/admin"
              className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition
                ${path.startsWith('/admin') ? 'text-gold-400' : 'text-gold-400/80 hover:text-gold-400'}`}>
              ⚙️ Admin
            </Link>
          )}
        </div>
        <div className="flex items-center gap-2">
          {ready && profile ? (
            <>
              <Link href="/profile" className="pill-gold">
                {fmtCoins(profile.balance)}
              </Link>
              <Link href="/profile" className="pill">Lv {profile.level.level}</Link>
              <button onClick={() => { clearSession(); router.push('/'); }}
                className="btn-ghost hidden sm:inline-flex">Sign out</button>
            </>
          ) : ready ? (
            <Link href="/login" className="btn-primary">Sign in</Link>
          ) : null}
          <button className="md:hidden btn-ghost px-2" onClick={() => setOpen(!open)}>☰</button>
        </div>
      </div>
      {open && (
        <div className="md:hidden border-t border-white/10 px-4 py-2 space-y-1">
          {LINKS.map(([href, label]) => (
            <Link key={href} href={href} onClick={() => setOpen(false)}
              className="block rounded-lg px-3 py-2 text-sm text-ink/80 hover:bg-white/5">
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}

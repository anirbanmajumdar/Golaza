'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { MatchCard } from '@/components/MatchCard';
import { Meter } from '@/components/ProbBar';
import { api, fmtCoins, type MatchRow, type Profile } from '@/lib/api';
import { useToken } from '@/lib/auth';

export default function Dashboard() {
  const { token, ready } = useToken();
  const router = useRouter();
  const [p, setP] = useState<Profile | null>(null);
  const [upcoming, setUpcoming] = useState<MatchRow[]>([]);
  const [bonus, setBonus] = useState<string | null>(null);

  useEffect(() => { if (ready && !token) router.replace('/login'); }, [ready, token, router]);
  useEffect(() => {
    if (!token) return;
    api.get<Profile>('/me', token).then(setP);
    api.get<MatchRow[]>('/matches?status=scheduled').then(r =>
      setUpcoming(r.filter(m => m.home && m.away).slice(0, 6)));
  }, [token]);

  async function claim() {
    if (!token) return;
    const r = await api.post<{ claimed: boolean; amount?: number; message?: string }>(
      '/me/daily-bonus', undefined, token);
    setBonus(r.claimed ? `+${fmtCoins(r.amount!)} claimed!` : (r.message ?? 'Already claimed'));
    api.get<Profile>('/me', token).then(setP);
    window.dispatchEvent(new Event('golazo-auth'));
  }

  if (!p) return <p className="text-muted">Loading your locker room…</p>;
  const lv = p.level;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display text-3xl">Hey, {p.display_name} 👋</h1>
        <button className="btn-gold" onClick={claim}>🎁 Daily bonus</button>
      </div>
      {bonus && <div className="rounded-xl border border-gold-500/40 bg-gold-500/10 p-2 text-sm text-gold-400">{bonus}</div>}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card"><div className="text-xs text-muted">Balance</div>
          <div className="font-display text-2xl text-gold-400">{fmtCoins(p.balance)}</div></div>
        <div className="card"><div className="text-xs text-muted">Net profit</div>
          <div className={`font-display text-2xl ${p.stats.net_profit >= 0 ? 'text-grass-400' : 'text-red-300'}`}>
            {p.stats.net_profit >= 0 ? '+' : ''}{fmtCoins(p.stats.net_profit)}</div></div>
        <div className="card"><div className="text-xs text-muted">Hit rate</div>
          <div className="font-display text-2xl">{p.stats.hit_rate != null ? `${Math.round(p.stats.hit_rate * 100)}%` : '—'}</div>
          <div className="text-[11px] text-muted">{p.stats.bets_won}/{p.stats.bets_settled} settled</div></div>
        <div className="card"><div className="text-xs text-muted">Win streak</div>
          <div className="font-display text-2xl">{p.current_streak}🔥 <span className="text-sm text-muted">best {p.best_streak}</span></div></div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between text-sm">
          <span className="font-semibold">Level {lv.level}</span>
          <span className="text-muted">{lv.xp_into_level}/{lv.level_span} XP · {lv.xp_to_next} to next</span>
        </div>
        <div className="mt-2"><Meter value={lv.progress} color="#16c784" /></div>
      </div>

      <div className="flex flex-wrap gap-2">
        <Link href="/matches" className="btn-primary">Bet on matches</Link>
        <Link href="/simulator" className="btn-ghost">Run a simulation</Link>
        <Link href="/profile" className="btn-ghost">My profile & badges</Link>
        <Link href="/leaderboard" className="btn-ghost">Leaderboard</Link>
      </div>

      <div>
        <h2 className="mb-3 font-display text-2xl">Next up</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {upcoming.map(m => <MatchCard key={m.id} m={m} />)}
        </div>
      </div>
    </div>
  );
}

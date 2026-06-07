'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { BallMark } from '@/components/Logo';
import { Meter } from '@/components/ProbBar';
import { api, fmtCoins, type SimTeam } from '@/lib/api';

const FEATURES = [
  ['📊', 'A real model, not vibes', 'Every match is priced by an Elo-driven Dixon–Coles bivariate-Poisson model — full scoreline distributions, not guesses.'],
  ['🎲', 'Monte-Carlo the whole cup', 'Simulate all 104 matches thousands of times to get each nation\'s odds to escape the group, reach the final and lift the trophy.'],
  ['🧮', 'Edge, EV & Kelly', 'See the fair odds, your implied edge and the Kelly-optimal stake before every bet. Outsmart the model to profit.'],
  ['🔮', 'Skill, measured', 'Forecasts are graded with the Brier score — climb a leaderboard that rewards calibration, not just luck.'],
  ['🏆', 'Badges, streaks & levels', 'Daily bonuses, win streaks, achievement badges and XP levels keep the whole group hooked all summer.'],
  ['👥', 'Private friend leagues', 'Spin up a league, share a join code, and settle who really knows football once and for all.'],
];

export default function Home() {
  const [top, setTop] = useState<SimTeam[]>([]);
  useEffect(() => {
    api.get<{ ready: boolean; teams: SimTeam[] }>('/sim/tournament')
      .then(d => d.ready && setTop(d.teams.slice(0, 6))).catch(() => {});
  }, []);

  return (
    <div className="space-y-16">
      {/* hero */}
      <section className="pitch-stripes relative overflow-hidden rounded-3xl border border-white/10 px-6 py-14 text-center">
        <div className="mx-auto mb-5 flex justify-center"><BallMark size={72} /></div>
        <h1 className="font-display text-4xl sm:text-6xl tracking-tight">
          Predict the <span className="text-grass-400">World Cup</span>.<br />
          Beat the <span className="text-gold-400">model</span>.
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-muted">
          GOLAZO 2026 is a private, play-money prediction league for you and your
          friends — backed by genuine football analytics. Get your invite,
          claim {fmtCoins(10000)} in coins, and call all 104 matches.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <Link href="/login" className="btn-primary px-6 py-3 text-base">Sign in →</Link>
          <Link href="/simulator" className="btn-ghost px-6 py-3 text-base">Run a simulation</Link>
        </div>
        <p className="mt-4 text-xs text-muted">Invite-only · No real money · 48 teams · Jun 11 – Jul 19, 2026</p>
      </section>

      {/* live model snapshot */}
      {top.length > 0 && (
        <section>
          <h2 className="mb-4 font-display text-2xl">Title odds — straight from the simulator</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {top.map((t, i) => (
              <Link key={t.code} href={`/teams/${t.code}`} className="card card-hover flex items-center gap-3">
                <span className="font-display text-lg text-muted w-6">{i + 1}</span>
                <span className="text-3xl">{t.flag}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold">{t.name}</span>
                    <span className="pill-gold">{(t.p_champion * 100).toFixed(1)}%</span>
                  </div>
                  <div className="mt-2"><Meter value={t.p_champion / (top[0].p_champion || 1)} /></div>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* features */}
      <section>
        <h2 className="mb-4 font-display text-2xl">Why it&apos;s more than a bracket</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map(([icon, title, body]) => (
            <div key={title} className="card">
              <div className="mb-2 text-2xl">{icon}</div>
              <h3 className="font-semibold">{title}</h3>
              <p className="mt-1 text-sm text-muted">{body}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="card text-center">
        <h2 className="font-display text-2xl">Got your invite?</h2>
        <p className="mt-1 text-muted">Set your password from the email link, then sign in.</p>
        <Link href="/login" className="btn-gold mt-4 px-6 py-3 text-base">Sign in</Link>
      </section>
    </div>
  );
}

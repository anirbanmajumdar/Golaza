'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Meter } from '@/components/ProbBar';
import { api } from '@/lib/api';

interface Detail {
  code: string; name: string; group: string; flag: string; confederation: string;
  elo: number; elo_seed: number; fifa_pts: number; is_host: boolean;
  players: { name: string; position: string }[];
  simulation: Record<string, number>;
  group_table: { code: string; name: string; flag: string; elo: number }[];
  fixtures: { id: number; stage: string; home_code: string; away_code: string;
              kickoff: string; venue: string; status: string; score: string | null }[];
}

export default function TeamPage() {
  const { code } = useParams<{ code: string }>();
  const [d, setD] = useState<Detail | null>(null);
  useEffect(() => { api.get<Detail>(`/teams/${code}`).then(setD); }, [code]);
  if (!d) return <p className="text-muted">Loading…</p>;
  const s = d.simulation || {};

  const path: [string, number][] = [
    ['Advance from group', s.p_advance], ['Reach Round of 16', s.p_round_of_16],
    ['Reach Quarter-final', s.p_quarter], ['Reach Semi-final', s.p_semi],
    ['Reach Final', s.p_final], ['Win the World Cup', s.p_champion],
  ];

  return (
    <div className="space-y-6">
      <Link href="/teams" className="text-sm text-muted hover:text-ink">← All teams</Link>
      <div className="card flex items-center gap-4">
        <span className="text-6xl">{d.flag}</span>
        <div>
          <h1 className="font-display text-3xl">{d.name} {d.is_host && <span className="pill-gold">Host</span>}</h1>
          <p className="text-sm text-muted">Group {d.group} · {d.confederation} · Elo {d.elo}
            <span className="text-muted/70"> (seed {d.elo_seed})</span> · FIFA {d.fifa_pts}</p>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 font-display text-xl">Tournament path <span className="text-xs text-muted">(Monte-Carlo)</span></h2>
          <div className="space-y-2.5">
            {path.map(([label, v]) => (
              <div key={label}>
                <div className="flex justify-between text-sm">
                  <span className="text-muted">{label}</span>
                  <span className="font-semibold">{v != null ? `${(v * 100).toFixed(1)}%` : '—'}</span>
                </div>
                <Meter value={v ?? 0} color={label.includes('Win the') ? '#f5c518' : '#16c784'} />
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="card">
            <h2 className="mb-2 font-display text-xl">Star players</h2>
            <div className="flex flex-wrap gap-2">
              {d.players.map(p => (
                <span key={p.name} className="pill">{p.name} <span className="text-muted">{p.position}</span></span>
              ))}
            </div>
          </div>
          <div className="card">
            <h2 className="mb-2 font-display text-xl">Group {d.group}</h2>
            {d.group_table.map(t => (
              <Link key={t.code} href={`/teams/${t.code}`}
                className={`flex items-center justify-between rounded-lg px-2 py-1.5 text-sm hover:bg-white/5 ${t.code === d.code ? 'bg-white/5' : ''}`}>
                <span>{t.flag} {t.name}</span><span className="text-muted">Elo {t.elo}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="mb-3 font-display text-xl">Fixtures</h2>
        <div className="grid gap-2 sm:grid-cols-2">
          {d.fixtures.map(f => (
            <Link key={f.id} href={`/matches/${f.id}`}
              className="flex items-center justify-between rounded-lg border border-white/10 px-3 py-2 text-sm hover:bg-white/5">
              <span>{f.home_code} vs {f.away_code}</span>
              <span className="text-muted">{f.score ?? new Date(f.kickoff).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}

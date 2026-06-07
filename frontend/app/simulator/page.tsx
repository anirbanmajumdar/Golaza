'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Meter, ProbBar } from '@/components/ProbBar';
import { api, type SimTeam } from '@/lib/api';
import { useToken } from '@/lib/auth';

interface H2H {
  home: { code: string; name: string; flag: string; elo: number };
  away: { code: string; name: string; flag: string; elo: number };
  model: Record<string, any>;
  odds: Record<string, number>;
}

export default function SimulatorPage() {
  const { token } = useToken();
  const [sim, setSim] = useState<{ ready: boolean; n_sims?: number; teams: SimTeam[] } | null>(null);
  const [n, setN] = useState(2000);
  const [running, setRunning] = useState(false);
  const [teams, setTeams] = useState<{ code: string; name: string; flag: string }[]>([]);
  const [home, setHome] = useState('BRA');
  const [away, setAway] = useState('ARG');
  const [h2h, setH2h] = useState<H2H | null>(null);

  useEffect(() => {
    api.get<typeof sim>('/sim/tournament').then(setSim);
    api.get<typeof teams>('/teams').then(setTeams);
  }, []);
  useEffect(() => { runH2H(); /* eslint-disable-next-line */ }, [home, away]);

  async function runSim() {
    setRunning(true);
    try {
      const r = token
        ? await api.post<typeof sim>(`/sim/run?n=${n}`, undefined, token)
        : await api.get<typeof sim>(`/sim/tournament?n=${n}`);
      setSim(r);
    } finally { setRunning(false); }
  }
  function runH2H() {
    if (home && away && home !== away) api.get<H2H>(`/sim/h2h?home=${home}&away=${away}`).then(setH2h);
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl">Simulator</h1>
        <p className="text-muted">Roll the entire tournament thousands of times, or pit any two nations head-to-head.</p>
      </div>

      {/* tournament */}
      <section className="card">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-display text-xl">Tournament Monte-Carlo</h2>
          <div className="flex items-center gap-2">
            <select className="input !w-auto" value={n} onChange={e => setN(Number(e.target.value))}>
              {[1000, 2000, 5000, 10000].map(v => <option key={v} value={v}>{v.toLocaleString()} sims</option>)}
            </select>
            <button className="btn-primary" disabled={running} onClick={runSim}>
              {running ? 'Simulating…' : 'Run'}
            </button>
          </div>
        </div>
        {sim?.ready ? (
          <>
            <p className="mb-2 text-xs text-muted">{sim.n_sims?.toLocaleString()} simulations</p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-xs text-muted">
                  <tr><th className="py-1">#</th><th>Team</th><th>Grp</th>
                    <th className="text-right">Advance</th><th className="text-right">Semi</th>
                    <th className="text-right">Final</th><th className="text-right">🏆 Win</th>
                    <th className="text-right">Odds</th></tr>
                </thead>
                <tbody>
                  {sim.teams.slice(0, 24).map((t, i) => (
                    <tr key={t.code} className="border-t border-white/5">
                      <td className="py-1.5 text-muted">{i + 1}</td>
                      <td><Link href={`/teams/${t.code}`} className="hover:text-grass-400">{t.flag} {t.name}</Link></td>
                      <td className="text-muted">{t.group}</td>
                      <td className="text-right">{pct(t.p_advance)}</td>
                      <td className="text-right">{pct(t.p_semi)}</td>
                      <td className="text-right">{pct(t.p_final)}</td>
                      <td className="text-right font-semibold text-gold-400">{pct(t.p_champion)}</td>
                      <td className="text-right text-muted">{t.champion_odds ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : <p className="text-muted">Crunching…</p>}
      </section>

      {/* head to head */}
      <section className="card">
        <h2 className="mb-4 font-display text-xl">Head-to-head</h2>
        <div className="flex flex-wrap items-center gap-3">
          <TeamSelect value={home} onChange={setHome} teams={teams} />
          <span className="text-muted">vs</span>
          <TeamSelect value={away} onChange={setAway} teams={teams} />
        </div>
        {h2h && (
          <div className="mt-5 space-y-4">
            <div className="flex items-center justify-around">
              <div className="text-center"><div className="text-5xl">{h2h.home.flag}</div><div className="text-xs text-muted">Elo {h2h.home.elo}</div></div>
              <div className="text-center text-muted">
                <div className="font-display text-xl text-ink">{h2h.model.lambda_home} – {h2h.model.lambda_away}</div>
                <div className="text-xs">expected goals {h2h.model.exp_goals_home}–{h2h.model.exp_goals_away}</div>
              </div>
              <div className="text-center"><div className="text-5xl">{h2h.away.flag}</div><div className="text-xs text-muted">Elo {h2h.away.elo}</div></div>
            </div>
            <ProbBar segments={[
              { label: h2h.home.name, value: h2h.model.p_home, color: '#16c784' },
              { label: 'Draw', value: h2h.model.p_draw, color: '#8aa79b' },
              { label: h2h.away.name, value: h2h.model.p_away, color: '#f5c518' },
            ]} />
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <Odds label={h2h.home.name} v={h2h.odds.home} />
              <Odds label="Draw" v={h2h.odds.draw} />
              <Odds label={h2h.away.name} v={h2h.odds.away} />
            </div>
            <div className="flex flex-wrap gap-2 text-xs">
              {h2h.model.top_scores?.map((s: any) => (
                <span key={s.score} className="pill">{s.score} <span className="text-muted">{Math.round(s.prob * 100)}%</span></span>
              ))}
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

const pct = (v: number) => `${(v * 100).toFixed(1)}%`;
function TeamSelect({ value, onChange, teams }:
  { value: string; onChange: (v: string) => void; teams: { code: string; name: string; flag: string }[] }) {
  return (
    <select className="input !w-auto" value={value} onChange={e => onChange(e.target.value)}>
      {teams.map(t => <option key={t.code} value={t.code}>{t.flag} {t.name}</option>)}
    </select>
  );
}
function Odds({ label, v }: { label: string; v: number }) {
  return <div className="stat"><div className="truncate text-[11px] text-muted">{label}</div>
    <div className="font-display text-lg text-gold-400">{v?.toFixed(2)}</div></div>;
}

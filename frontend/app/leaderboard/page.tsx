'use client';

import { useEffect, useState } from 'react';
import { api, ApiError, fmtCoins } from '@/lib/api';
import { useToken } from '@/lib/auth';

interface Entry {
  rank: number; user_id: number; display_name: string; balance: number;
  net_profit: number; level: number; best_streak: number; skill: number | null;
  bets_settled: number;
}
interface LeagueRow { id: number; name: string; join_code: string; members: number; is_owner: boolean; }

const METRICS: [string, string, (e: Entry) => string][] = [
  ['balance', 'Balance', e => fmtCoins(e.balance)],
  ['net_profit', 'Profit', e => `${e.net_profit >= 0 ? '+' : ''}${fmtCoins(e.net_profit)}`],
  ['skill', 'Forecast skill', e => e.skill != null ? e.skill.toFixed(3) : '—'],
  ['level', 'Level', e => `Lv ${e.level}`],
  ['streak', 'Best streak', e => `${e.best_streak}🔥`],
];

export default function LeaderboardPage() {
  const { token } = useToken();
  const [metric, setMetric] = useState('balance');
  const [entries, setEntries] = useState<Entry[]>([]);
  const [leagues, setLeagues] = useState<LeagueRow[]>([]);
  const [name, setName] = useState('');
  const [code, setCode] = useState('');
  const [msg, setMsg] = useState<string | null>(null);

  const fmt = METRICS.find(m => m[0] === metric)![2];

  useEffect(() => {
    api.get<{ entries: Entry[] }>(`/leaderboard?metric=${metric}`).then(d => setEntries(d.entries));
  }, [metric]);
  useEffect(() => { if (token) api.get<LeagueRow[]>('/leagues', token).then(setLeagues); }, [token]);

  async function createLeague() {
    if (!name || !token) return;
    try { const r = await api.post<LeagueRow>('/leagues', { name }, token);
      setMsg(`Created “${r.name}” — share code ${r.join_code}`); setName('');
      api.get<LeagueRow[]>('/leagues', token).then(setLeagues);
    } catch (e) { setMsg(e instanceof ApiError ? e.message : String(e)); }
  }
  async function joinLeague() {
    if (!code || !token) return;
    try { const r = await api.post<LeagueRow>('/leagues/join', { code }, token);
      setMsg(`Joined “${r.name}”`); setCode('');
      api.get<LeagueRow[]>('/leagues', token).then(setLeagues);
    } catch (e) { setMsg(e instanceof ApiError ? e.message : String(e)); }
  }

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">Leaderboard</h1>

      <div className="flex flex-wrap gap-2">
        {METRICS.map(([m, label]) => (
          <button key={m} onClick={() => setMetric(m)}
            className={`pill ${metric === m ? '!bg-grass-500 !text-pitch-900' : ''}`}>{label}</button>
        ))}
      </div>

      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-muted">
            <tr><th className="py-1 w-10">#</th><th>Player</th>
              <th className="text-right">{METRICS.find(m => m[0] === metric)![1]}</th>
              <th className="text-right hidden sm:table-cell">Settled</th></tr>
          </thead>
          <tbody>
            {entries.map(e => (
              <tr key={e.user_id} className="border-t border-white/5">
                <td className="py-2">{e.rank === 1 ? '🥇' : e.rank === 2 ? '🥈' : e.rank === 3 ? '🥉' : e.rank}</td>
                <td className="font-medium">{e.display_name}</td>
                <td className="text-right font-semibold text-gold-400">{fmt(e)}</td>
                <td className="text-right text-muted hidden sm:table-cell">{e.bets_settled}</td>
              </tr>
            ))}
            {entries.length === 0 && <tr><td colSpan={4} className="py-4 text-center text-muted">No ranked players yet.</td></tr>}
          </tbody>
        </table>
        {metric === 'skill' && <p className="mt-2 text-xs text-muted">Forecast skill = Brier Skill Score vs a coin-flip prior (needs 5+ settled 1X2 bets). Higher is sharper.</p>}
      </div>

      {/* leagues */}
      <section className="space-y-3">
        <h2 className="font-display text-2xl">Private leagues</h2>
        {token ? (
          <>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="card flex gap-2">
                <input className="input" placeholder="New league name" value={name} onChange={e => setName(e.target.value)} />
                <button className="btn-primary whitespace-nowrap" onClick={createLeague}>Create</button>
              </div>
              <div className="card flex gap-2">
                <input className="input" placeholder="Join code" value={code} onChange={e => setCode(e.target.value.toUpperCase())} />
                <button className="btn-ghost whitespace-nowrap" onClick={joinLeague}>Join</button>
              </div>
            </div>
            {msg && <div className="rounded-xl border border-grass-500/30 bg-grass-500/10 p-2 text-sm text-grass-400">{msg}</div>}
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {leagues.map(l => (
                <LeagueCard key={l.id} l={l} token={token!} onShared={setMsg} />
              ))}
            </div>
          </>
        ) : <p className="text-muted">Sign in to create or join a friends league.</p>}
      </section>
    </div>
  );
}

function LeagueCard({ l, token, onShared }:
  { l: LeagueRow; token: string; onShared: (m: string) => void }) {
  const [link, setLink] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);

  async function share() {
    setBusy(true);
    try {
      const r = await api.get<{ link: string }>(`/leagues/${l.id}/invite-link`, token);
      setLink(r.link);
      try {
        await navigator.clipboard.writeText(r.link);
        setCopied(true); onShared('Invite link copied — send it to your friends!');
      } catch { onShared('Invite link ready — copy it below.'); }
    } catch (e) { onShared(e instanceof ApiError ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="card space-y-2">
      <div className="flex items-center justify-between">
        <span className="font-semibold">{l.name}</span>
        {l.is_owner && <span className="pill-gold">owner</span>}
      </div>
      <div className="text-xs text-muted">{l.members} members · code <code className="text-ink">{l.join_code}</code></div>
      <button className="btn-ghost w-full" disabled={busy} onClick={share}>
        {busy ? 'Generating…' : copied ? '✓ Link copied' : '🔗 Share invite link'}
      </button>
      {link && (
        <input readOnly value={link} onFocus={e => e.currentTarget.select()}
          className="input text-xs" />
      )}
      <p className="text-[11px] text-muted">
        Friends open the link, set a password, and are added to this league automatically.
      </p>
    </div>
  );
}

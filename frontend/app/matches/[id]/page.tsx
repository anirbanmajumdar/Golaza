'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect, useState } from 'react';
import { ProbBar } from '@/components/ProbBar';
import { api, ApiError, fmtCoins, OUTCOME_COLORS, type Quotes } from '@/lib/api';
import { useToken } from '@/lib/auth';

interface Detail {
  id: number; stage: string; group?: string; stage_label?: string;
  kickoff: string; venue: string; status: string;
  home_goals: number | null; away_goals: number | null; result: string | null;
  quotes: Quotes;
}
interface Pick { market: string; selection: string; label: string; odds: number; prob: number; }
interface Analysis {
  odds: number; model_prob: number; user_prob: number; edge_vs_model: number;
  expected_value_per_coin: number; expected_value_on_stake: number;
  kelly_fraction: number; half_kelly_pct: number; verdict: string;
}

export default function MatchDetail() {
  const { id } = useParams<{ id: string }>();
  const { token } = useToken();
  const [d, setD] = useState<Detail | null>(null);
  const [pick, setPick] = useState<Pick | null>(null);
  const [stake, setStake] = useState(500);
  const [confidence, setConfidence] = useState(60);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    api.get<Detail>(`/matches/${id}`).then(setD);
  }, [id]);
  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!pick) { setAnalysis(null); return; }
    const t = setTimeout(() => {
      api.post<Analysis>('/bets/analyze', {
        match_id: Number(id), market: pick.market, selection: pick.selection,
        confidence, stake,
      }).then(setAnalysis).catch(() => setAnalysis(null));
    }, 200);
    return () => clearTimeout(t);
  }, [pick, confidence, stake, id]);

  async function place() {
    if (!pick || !token) return;
    setErr(null); setMsg(null);
    try {
      const r = await api.post<{ balance: number }>('/bets', {
        match_id: Number(id), market: pick.market, selection: pick.selection,
        stake, confidence,
      }, token);
      setMsg(`Bet placed! New balance ${fmtCoins(r.balance)}.`);
      setPick(null);
      window.dispatchEvent(new Event('golazo-auth'));
    } catch (e) { setErr(e instanceof ApiError ? e.message : String(e)); }
  }

  if (!d) return <p className="text-muted">Loading…</p>;
  const q = d.quotes;
  const m = q.model || {};
  const finished = d.status === 'finished';

  return (
    <div className="space-y-6">
      <Link href="/matches" className="text-sm text-muted hover:text-ink">← Match Centre</Link>

      {/* header */}
      <div className="card">
        <div className="mb-3 flex items-center justify-between text-xs text-muted">
          <span className="pill">{d.group ? `Group ${d.group}` : (d.stage_label || d.stage)}</span>
          <span>{new Date(d.kickoff).toLocaleString()} · {d.venue}</span>
        </div>
        <div className="flex items-center justify-around">
          <TeamHead flag={q.home?.flag} name={q.home?.name} elo={q.home?.elo} />
          <div className="text-center">
            {finished
              ? <div className="font-display text-4xl text-gold-400">{d.home_goals}–{d.away_goals}</div>
              : <div className="text-muted">vs</div>}
            {q.home_advantage ? <div className="mt-1 text-[11px] text-grass-400">home edge +{Math.round(q.home_advantage)} Elo</div> : null}
          </div>
          <TeamHead flag={q.away?.flag} name={q.away?.name} elo={q.away?.elo} />
        </div>
      </div>

      {/* model panel */}
      {q.available && (
        <div className="card">
          <h2 className="mb-3 font-display text-xl">Model read</h2>
          <ProbBar segments={[
            { label: q.home?.name ?? 'Home', value: m.p_home as number, color: '#16c784' },
            { label: 'Draw', value: m.p_draw as number, color: '#8aa79b' },
            { label: q.away?.name ?? 'Away', value: m.p_away as number, color: '#f5c518' },
          ]} />
          <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Stat label="Exp. goals" value={`${m.exp_goals_home} – ${m.exp_goals_away}`} />
            <Stat label="Over 2.5" value={`${Math.round((m.p_over_2_5 as number) * 100)}%`} />
            <Stat label="Both score" value={`${Math.round((m.p_btts as number) * 100)}%`} />
            <Stat label="λ (rates)" value={`${m.lambda_home} / ${m.lambda_away}`} />
          </div>
          {Array.isArray((m as any).top_scores) && (
            <div className="mt-3 flex flex-wrap gap-2">
              {(m as any).top_scores.map((s: any) => (
                <span key={s.score} className="pill">{s.score}
                  <span className="text-muted">{Math.round(s.prob * 100)}%</span></span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* markets */}
      {q.available ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="space-y-4 lg:col-span-2">
            {q.markets?.map(mk => (
              <div key={mk.market} className="card">
                <h3 className="mb-2 text-sm font-semibold text-muted">{mk.label}</h3>
                <div className={`grid gap-2 ${mk.selections.length === 3 ? 'grid-cols-3' : 'grid-cols-2'}`}>
                  {mk.selections.map(s => {
                    const active = pick?.market === mk.market && pick?.selection === s.key;
                    return (
                      <button key={s.key}
                        onClick={() => setPick({ market: mk.market, selection: s.key, label: `${mk.label}: ${s.label}`, odds: s.odds, prob: s.prob })}
                        className={`odds-btn ${active ? 'odds-btn-active' : ''}`}>
                        <div className="truncate text-xs text-muted">{s.label}</div>
                        <div className="font-display text-lg text-gold-400">{s.odds.toFixed(2)}</div>
                        <div className="text-[10px] text-muted">{Math.round(s.prob * 100)}% fair</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>

          {/* bet slip */}
          <div className="lg:sticky lg:top-20 h-fit">
            <div className="card border-gold-500/30">
              <h3 className="mb-3 font-display text-lg">Bet Slip</h3>
              {!pick ? (
                <p className="text-sm text-muted">Tap an odds button to build a bet.</p>
              ) : (
                <div className="space-y-3">
                  <div className="rounded-xl bg-white/5 p-3">
                    <div className="text-sm font-semibold">{pick.label}</div>
                    <div className="text-xs text-muted">@ {pick.odds.toFixed(2)} · model {Math.round(pick.prob * 100)}%</div>
                  </div>
                  <div>
                    <label className="text-xs text-muted">Stake</label>
                    <input type="number" className="input mt-1" value={stake} min={1}
                      onChange={e => setStake(Math.max(1, Number(e.target.value)))} />
                    <div className="mt-1 flex gap-1">
                      {[100, 500, 1000, 2500].map(v => (
                        <button key={v} className="pill" onClick={() => setStake(v)}>{v}</button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-muted">Your confidence: <span className="text-ink font-semibold">{confidence}%</span></label>
                    <input type="range" min={34} max={99} value={confidence} className="w-full accent-grass-500"
                      onChange={e => setConfidence(Number(e.target.value))} />
                  </div>

                  {analysis && (
                    <div className="space-y-1.5 rounded-xl border border-white/10 bg-white/[0.03] p-3 text-sm">
                      <Row k="To return" v={fmtCoins(Math.round(stake * pick.odds))} />
                      <Row k="Your edge vs model" v={`${(analysis.edge_vs_model * 100).toFixed(1)}%`}
                           good={analysis.edge_vs_model > 0} />
                      <Row k="Expected value" v={`${analysis.expected_value_on_stake > 0 ? '+' : ''}${analysis.expected_value_on_stake} ₲`}
                           good={analysis.expected_value_on_stake > 0} />
                      <Row k="Kelly stake" v={`${analysis.half_kelly_pct.toFixed(1)}% bankroll (½)`} />
                      <div className={`pt-1 text-xs font-semibold ${analysis.expected_value_per_coin > 0 ? 'text-grass-400' : 'text-gold-400'}`}>
                        {analysis.verdict}
                      </div>
                    </div>
                  )}

                  {token ? (
                    <button className="btn-primary w-full" onClick={place}>Place ₲{stake} bet</button>
                  ) : (
                    <Link href="/login" className="btn-gold w-full">Sign in to bet</Link>
                  )}
                </div>
              )}
              {msg && <div className="mt-3 rounded-xl border border-grass-500/40 bg-grass-500/10 p-2 text-sm text-grass-400">{msg}</div>}
              {err && <div className="mt-3 rounded-xl border border-red-500/40 bg-red-500/10 p-2 text-sm text-red-300">{err}</div>}
            </div>
          </div>
        </div>
      ) : (
        <div className="card text-muted">{finished ? 'This match is settled.' : (q.reason || 'Markets not open yet.')}</div>
      )}
    </div>
  );
}

function TeamHead({ flag, name, elo }: { flag?: string; name?: string; elo?: number }) {
  return (
    <div className="text-center">
      <div className="text-5xl">{flag ?? '🏳️'}</div>
      <div className="mt-1 font-semibold">{name ?? 'TBD'}</div>
      {elo ? <div className="text-xs text-muted">Elo {elo}</div> : null}
    </div>
  );
}
function Stat({ label, value }: { label: string; value: string }) {
  return <div className="stat"><div className="text-[11px] text-muted">{label}</div><div className="font-semibold">{value}</div></div>;
}
function Row({ k, v, good }: { k: string; v: string; good?: boolean }) {
  return <div className="flex justify-between"><span className="text-muted">{k}</span>
    <span className={good === undefined ? '' : good ? 'text-grass-400' : 'text-gold-400'}>{v}</span></div>;
}

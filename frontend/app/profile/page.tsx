'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { api, fmtCoins, type Profile } from '@/lib/api';
import { useToken } from '@/lib/auth';

interface Badge { code: string; name: string; emoji: string; description: string;
  xp_reward: number; coin_reward: number; unlocked: boolean; }
interface Bet { id: number; market: string; selection: string; stake: number; odds: number;
  status: string; payout: number; model_prob: number; brier: number | null; created_at: string; }
interface Ledger { ts: string; kind: string; amount: number; balance_after: number; memo: string | null; }

export default function ProfilePage() {
  const { token, ready } = useToken();
  const router = useRouter();
  const [p, setP] = useState<Profile | null>(null);
  const [badges, setBadges] = useState<Badge[]>([]);
  const [bets, setBets] = useState<Bet[]>([]);
  const [ledger, setLedger] = useState<Ledger[]>([]);
  const [tab, setTab] = useState<'bets' | 'ledger'>('bets');

  useEffect(() => { if (ready && !token) router.replace('/login'); }, [ready, token, router]);
  useEffect(() => {
    if (!token) return;
    api.get<Profile>('/me', token).then(setP);
    api.get<Badge[]>('/me/badges', token).then(setBadges);
    api.get<Bet[]>('/me/bets', token).then(setBets);
    api.get<Ledger[]>('/me/ledger', token).then(setLedger);
  }, [token]);

  if (!p) return <p className="text-muted">Loading…</p>;
  const s = p.stats;
  const unlocked = badges.filter(b => b.unlocked).length;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-3xl">{p.display_name}</h1>
          <p className="text-sm text-muted">{p.email} · Level {p.level.level}</p>
        </div>
        <div className="text-right">
          <div className="font-display text-2xl text-gold-400">{fmtCoins(p.balance)}</div>
          <div className="text-xs text-muted">balance</div>
        </div>
      </div>

      <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
        <Stat label="Bets placed" v={`${s.bets_placed}`} />
        <Stat label="Hit rate" v={s.hit_rate != null ? `${Math.round(s.hit_rate * 100)}%` : '—'} />
        <Stat label="ROI" v={s.roi != null ? `${(s.roi * 100).toFixed(1)}%` : '—'} good={s.roi != null ? s.roi >= 0 : undefined} />
        <Stat label="Forecast skill" v={s.brier_skill_score != null ? s.brier_skill_score.toFixed(3) : '—'} good={s.brier_skill_score != null ? s.brier_skill_score > 0 : undefined} />
      </div>

      <section>
        <h2 className="mb-3 font-display text-2xl">Badges <span className="text-sm text-muted">{unlocked}/{badges.length}</span></h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {badges.map(b => (
            <div key={b.code} className={`card ${b.unlocked ? 'border-gold-500/40' : 'opacity-50'}`}>
              <div className="flex items-center gap-3">
                <span className="text-3xl">{b.unlocked ? b.emoji : '🔒'}</span>
                <div>
                  <div className="font-semibold">{b.name}</div>
                  <div className="text-xs text-muted">{b.description}</div>
                  <div className="mt-1 text-[11px] text-grass-400">+{b.xp_reward} XP{b.coin_reward ? ` · +${fmtCoins(b.coin_reward)}` : ''}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section>
        <div className="mb-3 flex gap-2">
          <button onClick={() => setTab('bets')} className={`pill ${tab === 'bets' ? '!bg-grass-500 !text-pitch-900' : ''}`}>My bets</button>
          <button onClick={() => setTab('ledger')} className={`pill ${tab === 'ledger' ? '!bg-grass-500 !text-pitch-900' : ''}`}>Coin history</button>
        </div>
        <div className="card overflow-x-auto">
          {tab === 'bets' ? (
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted"><tr>
                <th className="py-1">Market</th><th>Pick</th><th className="text-right">Stake</th>
                <th className="text-right">Odds</th><th className="text-right">Status</th><th className="text-right">Payout</th></tr></thead>
              <tbody>
                {bets.map(b => (
                  <tr key={b.id} className="border-t border-white/5">
                    <td className="py-1.5 text-muted">{b.market}</td>
                    <td className="font-medium">{b.selection}</td>
                    <td className="text-right">{b.stake}</td>
                    <td className="text-right">{b.odds.toFixed(2)}</td>
                    <td className={`text-right ${b.status === 'won' ? 'text-grass-400' : b.status === 'lost' ? 'text-red-300' : 'text-muted'}`}>{b.status}</td>
                    <td className="text-right text-gold-400">{b.payout || '—'}</td>
                  </tr>
                ))}
                {bets.length === 0 && <tr><td colSpan={6} className="py-4 text-center text-muted">No bets yet.</td></tr>}
              </tbody>
            </table>
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-xs text-muted"><tr>
                <th className="py-1">When</th><th>Type</th><th>Memo</th>
                <th className="text-right">Δ</th><th className="text-right">Balance</th></tr></thead>
              <tbody>
                {ledger.map((l, i) => (
                  <tr key={i} className="border-t border-white/5">
                    <td className="py-1.5 text-muted">{new Date(l.ts).toLocaleDateString()}</td>
                    <td>{l.kind}</td><td className="text-muted">{l.memo}</td>
                    <td className={`text-right ${l.amount >= 0 ? 'text-grass-400' : 'text-red-300'}`}>{l.amount >= 0 ? '+' : ''}{l.amount}</td>
                    <td className="text-right text-muted">{l.balance_after}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, v, good }: { label: string; v: string; good?: boolean }) {
  return <div className="stat"><div className="text-[11px] text-muted">{label}</div>
    <div className={`font-display text-xl ${good === undefined ? '' : good ? 'text-grass-400' : 'text-red-300'}`}>{v}</div></div>;
}

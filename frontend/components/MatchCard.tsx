import Link from 'next/link';
import { type MatchRow } from '@/lib/api';
import { ProbBar } from './ProbBar';

function when(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) +
    ' · ' + d.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
}

export function MatchCard({ m }: { m: MatchRow }) {
  const tbd = !m.home || !m.away;
  return (
    <Link href={`/matches/${m.id}`} className="card card-hover block">
      <div className="mb-2 flex items-center justify-between text-xs text-muted">
        <span className="pill">{m.group ? `Group ${m.group}` : (m.stage_label || m.stage)}</span>
        <span>{when(m.kickoff)}</span>
      </div>

      <div className="flex items-center justify-between gap-2">
        <Side flag={m.home?.flag} name={m.home?.name ?? 'TBD'} />
        <div className="text-center">
          {m.status === 'finished' ? (
            <div className="font-display text-2xl text-gold-400">
              {m.home_goals}–{m.away_goals}
            </div>
          ) : (
            <div className="text-xs font-semibold text-muted">vs</div>
          )}
        </div>
        <Side flag={m.away?.flag} name={m.away?.name ?? 'TBD'} right />
      </div>

      {!tbd && m.model && m.status !== 'finished' && (
        <div className="mt-3">
          <ProbBar showLegend={false} segments={[
            { label: '1', value: m.model.p_home, color: '#16c784' },
            { label: 'X', value: m.model.p_draw, color: '#8aa79b' },
            { label: '2', value: m.model.p_away, color: '#f5c518' },
          ]} />
          <div className="mt-1 flex justify-between text-[11px] text-muted">
            <span>{Math.round(m.model.p_home * 100)}%</span>
            <span>{Math.round(m.model.p_draw * 100)}% draw</span>
            <span>{Math.round(m.model.p_away * 100)}%</span>
          </div>
        </div>
      )}
      <div className="mt-2 text-[11px] text-muted">{m.venue}</div>
    </Link>
  );
}

function Side({ flag, name, right }: { flag?: string; name: string; right?: boolean }) {
  return (
    <div className={`flex flex-1 items-center gap-2 ${right ? 'flex-row-reverse text-right' : ''}`}>
      <span className="text-2xl">{flag ?? '🏳️'}</span>
      <span className="text-sm font-semibold leading-tight">{name}</span>
    </div>
  );
}

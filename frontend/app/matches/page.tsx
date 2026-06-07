'use client';

import { useState } from 'react';
import { MatchCard } from '@/components/MatchCard';
import { Async, Empty } from '@/components/State';
import { api, type MatchRow } from '@/lib/api';
import { useFetch } from '@/lib/hooks';

const STAGES = [
  ['group', 'Groups'], ['R32', 'Round of 32'], ['R16', 'Round of 16'],
  ['QF', 'Quarters'], ['SF', 'Semis'], ['FIN', 'Final'],
];
const GROUPS = 'ABCDEFGHIJKL'.split('');

export default function MatchesPage() {
  const [stage, setStage] = useState('group');
  const [group, setGroup] = useState<string | null>(null);

  const state = useFetch<MatchRow[]>(() => {
    const q = new URLSearchParams({ stage });
    if (stage === 'group' && group) q.set('group', group);
    return api.get<MatchRow[]>(`/matches?${q}`);
  }, [stage, group]);

  return (
    <div className="space-y-5">
      <h1 className="font-display text-3xl">Match Centre</h1>

      <div className="flex flex-wrap gap-2">
        {STAGES.map(([s, label]) => (
          <button key={s} onClick={() => { setStage(s); setGroup(null); }}
            className={`pill ${stage === s ? '!bg-grass-500 !text-pitch-900' : ''}`}>
            {label}
          </button>
        ))}
      </div>

      {stage === 'group' && (
        <div className="flex flex-wrap gap-1.5">
          <button onClick={() => setGroup(null)}
            className={`pill ${!group ? '!bg-gold-500 !text-pitch-900' : ''}`}>All</button>
          {GROUPS.map(g => (
            <button key={g} onClick={() => setGroup(g)}
              className={`pill ${group === g ? '!bg-gold-500 !text-pitch-900' : ''}`}>{g}</button>
          ))}
        </div>
      )}

      <Async state={state} retryLabel="Loading fixtures…">
        {(matches) => matches.length === 0 ? (
          <Empty message="No matches here yet — knockout participants are decided once the groups finish." />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {matches.map(m => <MatchCard key={m.id} m={m} />)}
          </div>
        )}
      </Async>
    </div>
  );
}

'use client';

import Link from 'next/link';
import { api } from '@/lib/api';
import { useFetch } from '@/lib/hooks';
import { Async, Empty } from '@/components/State';

interface T {
  code: string; name: string; group: string; flag: string; confederation: string;
  elo: number; fifa_pts: number; is_host: boolean;
  p_advance: number | null; p_champion: number | null; champion_odds: number | null;
}

export default function TeamsPage() {
  const state = useFetch<T[]>(() => api.get<T[]>('/teams'), []);

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl">The 48</h1>
      <Async state={state} retryLabel="Loading teams & title odds…">
        {(teams) => {
          if (!teams.length) return <Empty message="No teams seeded yet." />;
          const groups = 'ABCDEFGHIJKL'.split('').map(g => ({
            g, teams: teams.filter(t => t.group === g),
          })).filter(x => x.teams.length);
          return (
            <div className="space-y-6">
              {groups.map(({ g, teams }) => (
                <div key={g}>
                  <h2 className="mb-2 font-display text-lg text-grass-400">Group {g}</h2>
                  <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
                    {teams.map(t => (
                      <Link key={t.code} href={`/teams/${t.code}`} className="card card-hover">
                        <div className="flex items-center gap-2">
                          <span className="text-3xl">{t.flag}</span>
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1 font-semibold">
                              <span className="truncate">{t.name}</span>
                              {t.is_host && <span className="pill-gold !py-0">host</span>}
                            </div>
                            <div className="text-[11px] text-muted">{t.confederation} · Elo {t.elo}</div>
                          </div>
                        </div>
                        {t.p_champion !== null && (
                          <div className="mt-2 flex justify-between text-xs">
                            <span className="text-muted">Advance {Math.round((t.p_advance ?? 0) * 100)}%</span>
                            <span className="pill-grass">🏆 {((t.p_champion ?? 0) * 100).toFixed(1)}%</span>
                          </div>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          );
        }}
      </Async>
    </div>
  );
}

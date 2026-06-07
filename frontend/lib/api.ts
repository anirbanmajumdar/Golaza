/* Typed fetch wrapper around the FastAPI backend via the /api proxy
 * (configured in next.config.mjs, so no CORS in the browser). */

const BASE = '/api';

export class ApiError extends Error {
  constructor(public status: number, message: string, public body?: unknown) {
    super(message);
  }
}

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

async function request<T>(method: Method, path: string, body?: unknown,
                          token?: string | null): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, {
      method, headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      cache: 'no-store',
    });
  } catch {
    throw new ApiError(0, 'Cannot reach the GOLAZO server. Is the backend running?');
  }
  const text = await res.text();
  const json = text ? JSON.parse(text) : null;
  if (!res.ok) throw new ApiError(res.status, json?.detail ?? res.statusText, json);
  return json as T;
}

export const api = {
  get: <T>(p: string, t?: string | null) => request<T>('GET', p, undefined, t),
  post: <T>(p: string, b?: unknown, t?: string | null) => request<T>('POST', p, b, t),
};

// ── shared types ──
export interface TeamBrief { code: string; name: string; flag: string; elo?: number; }
export interface MatchModel { p_home: number; p_draw: number; p_away: number; }
export interface MatchRow {
  id: number; ext_id: string; stage: string; stage_label?: string;
  group?: string; kickoff: string; venue: string; status: string;
  home: TeamBrief | null; away: TeamBrief | null;
  home_goals: number | null; away_goals: number | null; result: string | null;
  model: MatchModel | null;
}
export interface Selection {
  key: string; label: string; prob: number; fair_odds: number; odds: number;
}
export interface Market { market: string; label: string; selections: Selection[]; }
export interface Quotes {
  available: boolean; reason?: string; match_id?: number;
  home?: TeamBrief; away?: TeamBrief; home_advantage?: number;
  model?: Record<string, number>; markets?: Market[]; overround?: number;
}
export interface SimTeam {
  code: string; name: string; flag: string; group: string;
  p_advance: number; p_round_of_16: number; p_quarter: number; p_semi: number;
  p_final: number; p_champion: number; p_group_winner: number;
  exp_group_points: number; champion_odds: number | null;
}
export interface Profile {
  id: number; email: string; display_name: string; balance: number;
  is_admin: boolean; status: string;
  level: { level: number; xp: number; xp_into_level: number; xp_to_next: number;
           level_span: number; progress: number };
  current_streak: number; best_streak: number;
  stats: { bets_placed: number; bets_settled: number; bets_won: number;
           hit_rate: number | null; coins_staked: number; net_profit: number;
           roi: number | null; brier_count: number; brier_skill_score: number | null };
}

export const OUTCOME_COLORS: Record<string, string> = {
  home: '#16c784', draw: '#8aa79b', away: '#f5c518',
  over: '#16c784', under: '#8aa79b', yes: '#16c784', no: '#f5c518',
};

export function fmtCoins(n: number): string {
  return '₲' + n.toLocaleString();
}

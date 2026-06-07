'use client';

import { useEffect, useRef, useState } from 'react';

// ── math helpers ──
const GRASS = '#16c784';
const GOLD = '#f5c518';
const MUTED = '#8aa79b';

function fact(n: number): number { let r = 1; for (let i = 2; i <= n; i++) r *= i; return r; }
function pois(k: number, lam: number): number { return Math.exp(-lam) * lam ** k / fact(k); }
function eloWin(d: number): number { return 1 / (1 + 10 ** (-d / 400)); }

function Slider({ label, min, max, step, value, set, fmt }:
  { label: string; min: number; max: number; step: number; value: number;
    set: (v: number) => void; fmt?: (v: number) => string }) {
  return (
    <label className="block text-sm">
      <span className="text-muted">{label}: </span>
      <span className="font-semibold text-ink">{fmt ? fmt(value) : value}</span>
      <input type="range" min={min} max={max} step={step} value={value}
        onChange={e => set(Number(e.target.value))}
        className="mt-1 w-full accent-grass-500" />
    </label>
  );
}

// ── 1. Elo → win probability logistic curve ──
export function EloCurve() {
  const [diff, setDiff] = useState(120);
  const W = 320, H = 170, pad = 28;
  const x = (d: number) => pad + ((d + 600) / 1200) * (W - pad - 8);
  const y = (p: number) => (H - 22) - p * (H - 40);
  const pts = [];
  for (let d = -600; d <= 600; d += 12) pts.push(`${x(d)},${y(eloWin(d))}`);
  const p = eloWin(diff);
  return (
    <div className="grid gap-4 sm:grid-cols-[1fr,220px] items-center">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <line x1={pad} y1={y(0.5)} x2={W - 8} y2={y(0.5)} stroke={MUTED} strokeDasharray="3 3" opacity="0.4" />
        <line x1={x(0)} y1={10} x2={x(0)} y2={H - 22} stroke={MUTED} strokeDasharray="3 3" opacity="0.4" />
        <polyline points={pts.join(' ')} fill="none" stroke={GRASS} strokeWidth="2.5" />
        <circle cx={x(diff)} cy={y(p)} r="5" fill={GOLD} />
        <text x={x(diff)} y={y(p) - 9} fill={GOLD} fontSize="11" textAnchor="middle">{(p * 100).toFixed(0)}%</text>
        <text x={pad} y={H - 6} fill={MUTED} fontSize="9">−600</text>
        <text x={W - 24} y={H - 6} fill={MUTED} fontSize="9">+600</text>
        <text x={x(0) + 3} y={H - 6} fill={MUTED} fontSize="9">Elo gap</text>
      </svg>
      <div className="space-y-2">
        <Slider label="Your team's Elo edge" min={-600} max={600} step={10} value={diff} set={setDiff}
          fmt={v => `${v > 0 ? '+' : ''}${v}`} />
        <p className="text-xs text-muted">Win-expectancy E = 1 / (1 + 10<sup>−Δ/400</sup>). A +120 edge ≈ {(eloWin(120) * 100).toFixed(0)}% expectancy.</p>
      </div>
    </div>
  );
}

// ── 2. Poisson goal distribution ──
export function PoissonBars() {
  const [lam, setLam] = useState(1.6);
  const ks = [0, 1, 2, 3, 4, 5, 6];
  const probs = ks.map(k => pois(k, lam));
  const max = Math.max(...probs);
  return (
    <div className="grid gap-4 sm:grid-cols-[1fr,220px] items-center">
      <div className="flex items-end gap-2 h-40">
        {ks.map(k => (
          <div key={k} className="flex flex-1 flex-col items-center justify-end">
            <span className="text-[10px] text-muted">{(probs[k] * 100).toFixed(0)}%</span>
            <div className="w-full rounded-t" style={{ height: `${(probs[k] / max) * 100}%`, background: GRASS }} />
            <span className="mt-1 text-xs text-muted">{k}</span>
          </div>
        ))}
      </div>
      <div className="space-y-2">
        <Slider label="Expected goals λ" min={0.2} max={3.5} step={0.1} value={lam} set={setLam} fmt={v => v.toFixed(1)} />
        <p className="text-xs text-muted">P(k goals) = e<sup>−λ</sup>·λ<sup>k</sup>/k!. The most likely scoreline shifts right as λ grows.</p>
      </div>
    </div>
  );
}

// ── 3. Dixon–Coles scoreline heatmap ──
export function ScoreHeatmap() {
  const [lh, setLh] = useState(1.7);
  const [la, setLa] = useState(1.0);
  const rho = -0.06, N = 6;
  const tau = (x: number, yy: number) => {
    if (x === 0 && yy === 0) return 1 - lh * la * rho;
    if (x === 0 && yy === 1) return 1 + lh * rho;
    if (x === 1 && yy === 0) return 1 + la * rho;
    if (x === 1 && yy === 1) return 1 - rho;
    return 1;
  };
  const m: number[][] = [];
  let tot = 0, ph = 0, pd = 0, pa = 0, best = { i: 0, j: 0, p: 0 };
  for (let i = 0; i < N; i++) { m[i] = []; for (let j = 0; j < N; j++) { const v = tau(i, j) * pois(i, lh) * pois(j, la); m[i][j] = v; tot += v; } }
  for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
    m[i][j] /= tot;
    if (i > j) ph += m[i][j]; else if (i < j) pa += m[i][j]; else pd += m[i][j];
    if (m[i][j] > best.p) best = { i, j, p: m[i][j] };
  }
  const maxc = Math.max(...m.flat());
  return (
    <div className="grid gap-4 lg:grid-cols-[260px,1fr] items-center">
      <div>
        <div className="grid" style={{ gridTemplateColumns: `auto repeat(${N},1fr)` }}>
          <div />
          {Array.from({ length: N }, (_, j) => <div key={j} className="text-center text-[10px] text-muted">{j}</div>)}
          {Array.from({ length: N }, (_, i) => (
            <FragmentRow key={i} i={i} N={N} m={m} maxc={maxc} best={best} />
          ))}
        </div>
        <div className="mt-1 text-[10px] text-muted text-center">away goals → · home goals ↓</div>
      </div>
      <div className="space-y-2">
        <Slider label="Home λ" min={0.3} max={3.2} step={0.1} value={lh} set={setLh} fmt={v => v.toFixed(1)} />
        <Slider label="Away λ" min={0.3} max={3.2} step={0.1} value={la} set={setLa} fmt={v => v.toFixed(1)} />
        <div className="flex gap-2 text-xs">
          <span className="pill-grass">Home {(ph * 100).toFixed(0)}%</span>
          <span className="pill">Draw {(pd * 100).toFixed(0)}%</span>
          <span className="pill-gold">Away {(pa * 100).toFixed(0)}%</span>
        </div>
        <p className="text-xs text-muted">Most likely score <b className="text-ink">{best.i}–{best.j}</b> ({(best.p * 100).toFixed(1)}%). The {N}×{N} grid is the joint pmf with the Dixon–Coles low-score correction.</p>
      </div>
    </div>
  );
}
function FragmentRow({ i, N, m, maxc, best }:
  { i: number; N: number; m: number[][]; maxc: number; best: { i: number; j: number } }) {
  return (
    <>
      <div className="pr-1 text-right text-[10px] text-muted self-center">{i}</div>
      {Array.from({ length: N }, (_, j) => {
        const a = m[i][j] / maxc;
        const isBest = best.i === i && best.j === j;
        return (
          <div key={j} title={`${i}-${j}: ${(m[i][j] * 100).toFixed(1)}%`}
            className="aspect-square rounded-[3px] m-[1px]"
            style={{ background: `rgba(22,199,132,${0.12 + a * 0.85})`, outline: isBest ? `2px solid ${GOLD}` : 'none' }} />
        );
      })}
    </>
  );
}

// ── 4. Monte-Carlo convergence (animated) ──
export function MonteCarlo() {
  const [trueP, setTrueP] = useState(0.17);
  const [run, setRun] = useState(0);          // bump to restart
  const [n, setN] = useState(0);
  const [est, setEst] = useState(0);
  const seqRef = useRef<number[]>([]);
  const raf = useRef<number>();
  const MAXN = 1500, W = 320, H = 170, pad = 28;

  useEffect(() => {
    seqRef.current = Array.from({ length: MAXN }, () => (Math.random() < trueP ? 1 : 0));
    let i = 0, hits = 0;
    const means: number[] = [];
    const step = () => {
      const batch = Math.max(1, Math.floor(i / 40) + 1);
      for (let b = 0; b < batch && i < MAXN; b++) { hits += seqRef.current[i]; i++; means.push(hits / i); }
      setN(i); setEst(hits / i); pathRef.current = means;
      if (i < MAXN) raf.current = requestAnimationFrame(step);
    };
    raf.current = requestAnimationFrame(step);
    return () => { if (raf.current) cancelAnimationFrame(raf.current); };
  }, [trueP, run]);

  const pathRef = useRef<number[]>([]);
  const means = pathRef.current;
  const x = (k: number) => pad + (k / MAXN) * (W - pad - 8);
  const y = (p: number) => (H - 22) - (p / 0.5) * (H - 40);
  const poly = means.filter((_, k) => k % 4 === 0).map((mn, k) => `${x(k * 4)},${y(Math.min(mn, 0.5))}`).join(' ');
  const band = 1 / Math.sqrt(Math.max(1, n));

  return (
    <div className="grid gap-4 sm:grid-cols-[1fr,220px] items-center">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <line x1={pad} y1={y(trueP)} x2={W - 8} y2={y(trueP)} stroke={GOLD} strokeDasharray="4 3" opacity="0.7" />
        <text x={W - 8} y={y(trueP) - 4} fill={GOLD} fontSize="9" textAnchor="end">true p = {(trueP * 100).toFixed(0)}%</text>
        <polyline points={poly} fill="none" stroke={GRASS} strokeWidth="2" />
        <text x={pad} y={H - 6} fill={MUTED} fontSize="9">1 sim</text>
        <text x={W - 24} y={H - 6} fill={MUTED} fontSize="9">{MAXN}</text>
      </svg>
      <div className="space-y-2">
        <Slider label="True probability" min={0.02} max={0.5} step={0.01} value={trueP} set={setTrueP} fmt={v => `${(v * 100).toFixed(0)}%`} />
        <div className="stat">
          <div className="text-[11px] text-muted">After {n.toLocaleString()} sims</div>
          <div className="font-display text-xl">{(est * 100).toFixed(1)}% <span className="text-xs text-muted">± {(band * 100).toFixed(1)}%</span></div>
        </div>
        <button className="btn-ghost w-full" onClick={() => setRun(r => r + 1)}>↻ Re-run</button>
        <p className="text-xs text-muted">The estimate wobbles, then homes in on the truth. Monte-Carlo error shrinks like 1/√N.</p>
      </div>
    </div>
  );
}

// ── 5. Kelly growth curve ──
export function KellyCurve() {
  const [p, setP] = useState(0.55);
  const [odds, setOdds] = useState(2.0);
  const b = odds - 1;
  const W = 320, H = 170, pad = 28;
  const g = (f: number) => p * Math.log(1 + f * b) + (1 - p) * Math.log(1 - f);
  const fStar = Math.max(0, Math.min(1, (p * b - (1 - p)) / b));
  const fs: number[] = []; for (let f = 0; f <= 0.99; f += 0.02) fs.push(f);
  const gmax = Math.max(...fs.map(g), g(fStar), 0.001);
  const gmin = Math.min(...fs.map(g), 0);
  const x = (f: number) => pad + f * (W - pad - 8);
  const y = (v: number) => (H - 22) - ((v - gmin) / (gmax - gmin || 1)) * (H - 40);
  const poly = fs.map(f => `${x(f)},${y(g(f))}`).join(' ');
  const ev = p * (odds - 1) - (1 - p);
  return (
    <div className="grid gap-4 sm:grid-cols-[1fr,220px] items-center">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
        <line x1={pad} y1={y(0)} x2={W - 8} y2={y(0)} stroke={MUTED} strokeDasharray="3 3" opacity="0.4" />
        <polyline points={poly} fill="none" stroke={fStar > 0 ? GRASS : '#e5484d'} strokeWidth="2.5" />
        {fStar > 0 && <>
          <line x1={x(fStar)} y1={10} x2={x(fStar)} y2={H - 22} stroke={GOLD} strokeDasharray="4 3" />
          <text x={x(fStar)} y={20} fill={GOLD} fontSize="10" textAnchor="middle">f* = {(fStar * 100).toFixed(0)}%</text>
        </>}
        <text x={pad} y={H - 6} fill={MUTED} fontSize="9">stake 0%</text>
        <text x={W - 28} y={H - 6} fill={MUTED} fontSize="9">100%</text>
      </svg>
      <div className="space-y-2">
        <Slider label="Your true win prob p" min={0.05} max={0.95} step={0.01} value={p} set={setP} fmt={v => `${(v * 100).toFixed(0)}%`} />
        <Slider label="Decimal odds offered" min={1.1} max={6} step={0.05} value={odds} set={setOdds} fmt={v => v.toFixed(2)} />
        <div className={`text-xs font-semibold ${ev > 0 ? 'text-grass-400' : 'text-red-300'}`}>
          EV {ev >= 0 ? '+' : ''}{ev.toFixed(3)}/coin · Kelly {(fStar * 100).toFixed(0)}% {fStar === 0 && '(no edge — don’t bet)'}
        </div>
        <p className="text-xs text-muted">Growth peaks at the Kelly fraction f* = (p·b − q)/b. Bet more and long-run growth falls; past 2f* you go broke.</p>
      </div>
    </div>
  );
}

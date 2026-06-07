'use client';

import { EloCurve, PoissonBars, ScoreHeatmap, MonteCarlo, KellyCurve } from '@/components/charts';

const SECTIONS = [
  {
    key: 'elo', icon: '📈', title: '1 · Elo ratings — measuring strength',
    body: 'Every nation carries an Elo rating. The probability that team A beats team B is the logistic curve',
    math: 'E_A = 1 / (1 + 10^(−(R_A − R_B + H) / 400))',
    note: 'H is home-field advantage in Elo points (~70, ≈ 0.4 goals), applied only to the host nations. After each result ratings exchange points, R′ = R + K·G·(W − E): K weights match importance, G dampens blowouts. Drag the slider to see how an Elo gap maps to win-expectancy.',
    chart: <EloCurve />,
  },
  {
    key: 'poisson', icon: '⚽', title: '2 · Poisson — how many goals?',
    body: 'A team that is expected to score λ goals actually scores k goals with Poisson probability',
    math: 'P(k) = e^(−λ) · λ^k / k!',
    note: 'Football goals are close to Poisson. The Elo gap sets each side’s λ. Slide λ and watch the goal distribution shift.',
    chart: <PoissonBars />,
  },
  {
    key: 'dc', icon: '🔢', title: '3 · Dixon–Coles — the scoreline matrix',
    body: 'Two independent Poissons under-count 0-0 and 1-1 draws, so Dixon & Coles (1997) multiply the low-score cells by a correction τ(ρ):',
    math: 'P(x, y) = τ_ρ(x, y) · Poisson(x; λ_h) · Poisson(y; λ_a)',
    note: 'The normalised grid is the joint distribution of every scoreline — and from it we read 1X2, over/under, both-teams-to-score and the most likely score. Set the two λ’s and explore.',
    chart: <ScoreHeatmap />,
  },
  {
    key: 'mc', icon: '🎲', title: '4 · Monte-Carlo — simulating the cup',
    body: 'We play all 104 matches thousands of times and count how often each team wins. The estimate of any probability converges as the number of simulations N grows:',
    math: 'P(event) ≈ (# sims with event) / N,   error ∝ 1/√N',
    note: 'Watch a single probability being estimated live — noisy at first, then converging on the truth. That’s why the tournament page runs thousands of sims.',
    chart: <MonteCarlo />,
  },
  {
    key: 'kelly', icon: '🧮', title: '5 · Odds, EV & Kelly — sizing the bet',
    body: 'Fair odds are o = 1/p. If you believe the true probability is p, your edge is EV = p·(o−1) − (1−p), and the growth-optimal stake is the Kelly fraction',
    math: 'f* = (p·(o − 1) − (1 − p)) / (o − 1)',
    note: 'The curve is your long-run log-growth versus how much of your bankroll you stake. It peaks exactly at f*. No edge (EV ≤ 0) → f* = 0, don’t bet. We suggest half-Kelly to tame variance.',
    chart: <KellyCurve />,
  },
  {
    key: 'brier', icon: '🔮', title: '6 · Brier score — grading your judgement',
    body: 'When you commit a probability vector over {home, draw, away}, we grade it with a strictly proper scoring rule you can only beat by being honest:',
    math: 'Brier = Σ_k (p_k − o_k)²        Skill = 1 − Brier_you / Brier_ref',
    note: 'o_k is the actual outcome (one-hot). Averaged over your settled bets and benchmarked against a coin-flip prior, this Brier Skill Score ranks forecasting ability independently of how many coins you wagered. The skill leaderboard rewards calibration, not luck.',
    chart: null,
  },
];

export default function SciencePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-3xl">The Science</h1>
        <p className="text-muted">GOLAZO prices every match with the same toolkit quants use to beat real
          sportsbooks. Every chart below is live — drag the sliders.</p>
      </div>

      {SECTIONS.map(s => (
        <div key={s.key} className="card space-y-3">
          <h2 className="font-display text-xl">{s.icon} {s.title}</h2>
          <p className="text-sm text-ink/90">{s.body}</p>
          <pre className="overflow-x-auto rounded-xl border border-white/10 bg-pitch-900/60 p-3 font-mono text-sm text-grass-400 whitespace-pre-wrap">{s.math}</pre>
          {s.chart && <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">{s.chart}</div>}
          <p className="text-sm text-muted">{s.note}</p>
        </div>
      ))}

      <div className="card text-xs text-muted">
        References: Elo (1978); Dixon &amp; Coles, <em>Modelling Association Football Scores</em> (JRSS-C, 1997);
        Kelly, <em>A New Interpretation of Information Rate</em> (1956); Brier (1950);
        Hvattum &amp; Arntzen, <em>Using ELO ratings for match result prediction</em> (2010).
      </div>
    </div>
  );
}

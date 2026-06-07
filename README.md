# ⚽ GOLAZO 2026 — World Cup Prediction League

A **private, play-money** World Cup 2026 prediction & betting league for you
and your friends, with a genuine quantitative engine under the hood. Get an
invite, claim ₲10,000 in coins, and call all **104 matches** of the
Canada · Mexico · USA 2026 World Cup.

> **Play money only.** GOLAZO uses virtual coins (₲). There is no deposit,
> withdrawal, or real-money wagering anywhere in the app.

**Stack:** Next.js 14 (App Router + Tailwind) · FastAPI + SQLModel (SQLite) ·
NumPy quant engine · Docker · one-command deploy.

---

## ✨ What makes it different

It's not a bracket pool — every market is priced by real football analytics
(explained interactively on the in-app **The Science** page):

| Layer | Model |
|------|-------|
| Team strength | **Elo ratings** — logistic win-expectancy, importance-weighted updates, host home-field edge |
| Match goals | **Dixon–Coles bivariate-Poisson** → full scoreline matrix → 1X2 / O-U 2.5 / BTTS / exact score |
| Tournament | **Monte-Carlo** over all 104 matches → P(advance / semi / final / champion) |
| Bet sizing | Fair odds, **Expected Value** & **Kelly** fraction shown on every slip |
| Skill ranking | **Brier score** / Brier Skill Score — rewards calibration, not luck |

### 🎮 Gamification
₲10k welcome bonus · daily bonus · XP & levels · win-streaks · 10 achievement
badges · leaderboards by **balance, profit, forecast-skill, level, streak** ·
**private friend leagues** with shareable join links.

### 🔐 Private & invite-only
Nobody self-registers. An **admin invites players by email**; the invitee
clicks a link to set a password. Login is email + password; password resets
are **OTP-driven** (code emailed). Leagues also have a **one-click share link**
(`/join?token=…`, auto-shortened via TinyURL) that creates the account and
auto-joins the league in a single step.

---

## 🗂 Architecture

```
golazo/
├── backend/   FastAPI + SQLModel (SQLite) + NumPy quant engine
│   └── app/
│       ├── quant/      elo · poisson (Dixon–Coles) · odds · simulate · scoring
│       ├── data/       48 teams · 12 real groups · 104-match calendar · star players
│       ├── models/     SQLModel tables (users, matches, bets, ledger, leagues…)
│       ├── services/   seed · market · betting · sim · gamification · url_shortener
│       └── routers/    auth · me · teams · matches · bets · sim · leaderboard · admin
├── frontend/  Next.js 14 (App Router) + Tailwind  — dark "pitch" theme
│   └── app/   landing · login · accept-invite · join · dashboard · matches
│              · teams · simulator · leaderboard · profile · science · admin
└── docker-compose.yml · docker-compose.prod.yml   one-command deploy
```

The frontend proxies `/api/*` to the backend, so the browser never deals with
CORS and only the frontend needs to be public.

---

## 🚀 Run locally

```bash
# backend  → http://localhost:8000  (interactive docs at /docs)
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend → http://localhost:3030   (new terminal)
cd frontend
npm install
npm run dev
```

The first admin is bootstrapped from `WCB_ADMIN_EMAILS` (default
`admin@example.com`). With no SMTP configured the app runs in **dev mode** —
OTP codes and invite links are returned by the API / shown on screen, so you
can sign in without a mail server:

1. Open `http://localhost:3030/login` → **Forgot password** → enter the admin
   email → use the shown dev code to set a password.
2. Sign in → **⚙️ Admin** → invite players, enter results, run simulations.

### Docker

```bash
cp .env.example .env        # set WCB_SECRET_KEY (+ SMTP for real email)
docker compose up --build   # frontend :3030, backend :8000
```

SQLite lives in the `golazo_data` volume, so results/bets persist.

---

## ☁️ Deploy to any cloud

GOLAZO is just two containers + SQLite, so it runs on the smallest VM:

```bash
cp .env.example .env        # set WCB_SECRET_KEY, WCB_PUBLIC_BASE_URL, SMTP
docker compose -f docker-compose.prod.yml up -d --build
```

Put a reverse proxy (Caddy or nginx) in front for automatic HTTPS and point
your domain at the VM. Only the frontend needs to be public — it proxies
`/api/*` to the backend over the internal Docker network. Set
`WCB_DEV_ECHO_OTP=false` in production so OTP codes are never returned by the API.

### Refresh team ratings (optional)
```bash
docker compose exec backend python -m app.scripts.refresh_ratings
```
Pulls live World-Football Elo, silently keeping the seeds if egress is blocked.

---

## ⚙️ Configuration (env vars, prefix `WCB_`)

| Var | Default | Purpose |
|---|---|---|
| `WCB_SECRET_KEY` | dev value | JWT signing — **set a random value in prod** |
| `WCB_ADMIN_EMAILS` | `["admin@example.com"]` | bootstrapped admin accounts |
| `WCB_PUBLIC_BASE_URL` | `http://localhost:3030` | base for invite/reset links |
| `WCB_SMTP_HOST/PORT/USER/PASSWORD/FROM` | — | email (e.g. Gmail App Password) |
| `WCB_DEV_ECHO_OTP` | `true` | echo OTP/links when SMTP is unset (**false in prod**) |
| `WCB_SHORTEN_LINKS` | `true` | shorten invite/join links via TinyURL |
| `WCB_STARTING_BALANCE` | `10000` | welcome coins |

---

## 🧮 Settling matches

Results are entered by an admin (**Admin → Results**, or the API below), which
settles all open bets, updates Elo, and refreshes the simulation:

```bash
# POST /admin/matches/{id}/settle       {"home_goals":2,"away_goals":1}
# POST /admin/matches/{id}/auto-settle   (random scoreline from the model — demos)
```

Full interactive API docs at `https://<host>/api/docs`.

---

*Built for friends. Not affiliated with FIFA. Play money only.*

"""GOLAZO 2026 — FastAPI entry point.

A friends-only, PLAY-MONEY World Cup 2026 prediction league with a real
quantitative core (Elo + Dixon–Coles + Monte-Carlo + proper scoring).

Run locally:
    cd backend && pip install -r requirements.txt
    uvicorn app.main:app --reload
Docs at /docs.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from .core.config import settings
from .core.db import create_db_and_tables, engine
from .routers import admin, auth, bets, leaderboard, matches, me, sim, teams
from .services import seed

logging.basicConfig(level=logging.INFO,
                     format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger("golazo.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    create_db_and_tables()
    with Session(engine) as session:
        seed.run_all(session)
    log.info("GOLAZO 2026 ready ⚽")
    yield


app = FastAPI(
    title="GOLAZO 2026 API",
    version="1.0.0",
    description="Play-money World Cup 2026 prediction league. Elo + "
                "Dixon–Coles goal model · Monte-Carlo bracket · Kelly/EV · "
                "Brier skill scoring. Open /docs to explore.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["meta"])
def healthz():
    return {"status": "ok", "app": "golazo-2026"}


for r in (auth, me, teams, matches, bets, sim, leaderboard, admin):
    app.include_router(r.router)

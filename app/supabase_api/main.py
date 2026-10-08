"""Stel Sprint 6 samen; opslag en authenticatie gaan uitsluitend via Supabase."""

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from app.routers import general
from app.supabase_api.config import Settings
from app.supabase_api.handlers import register_error_handlers
from app.supabase_api.routers import auth, leaderboard, players, scores


def create_app(
    settings: Settings | None = None, *, http_transport: httpx.BaseTransport | None = None,
) -> FastAPI:
    settings = settings or Settings.from_env()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        settings.validate()
        yield

    app = FastAPI(
        title="Game Score API - Sprint 6 (Supabase)", version="6.0.0",
        description="Supabase Database, Supabase Auth en toegang per speler-eigenaar.",
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.http_transport = http_transport
    register_error_handlers(app)
    app.include_router(general.router)
    app.include_router(auth.router)
    app.include_router(players.router)
    app.include_router(scores.router)
    app.include_router(leaderboard.router)
    return app


app = create_app()

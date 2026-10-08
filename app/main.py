"""Stel de applicatie samen; endpoints en queries staan in hun eigen modules."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.database import Database
from app.handlers import register_error_handlers
from app.routers import general, leaderboard, players, scores


def create_app(db_path: Path | None = None) -> FastAPI:
    """Elke app heeft haar eigen database, zodat tests geen echte data wijzigen."""
    database = Database(db_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            database.initialize()
            yield
        finally:
            database.close()

    app = FastAPI(
        title="Game Score API - Sprint 5",
        description="Modulaire API voor spelers en scores met permanente SQLite-opslag.",
        version="5.0.0",
        lifespan=lifespan,
    )
    app.state.database = database
    register_error_handlers(app)
    app.include_router(general.router)
    app.include_router(players.router)
    app.include_router(scores.router)
    app.include_router(leaderboard.router)
    return app


app = create_app()

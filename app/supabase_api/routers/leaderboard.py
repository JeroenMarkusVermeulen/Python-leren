"""Dezelfde openbare ranglijst, nu berekend uit Supabase-data."""

from fastapi import APIRouter

from app.schemas.player import Player
from app.supabase_api.dependencies import ContextDep
from app.supabase_api.services.players import PlayerService


router = APIRouter(tags=["Players"])


@router.get("/leaderboard", response_model=list[Player])
def get_leaderboard(context: ContextDep) -> list[Player]:
    return PlayerService(context).leaderboard()

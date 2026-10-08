"""De ranglijst heeft een eigen router; sorteren gebeurt in de service."""

from fastapi import APIRouter

from app.dependencies import SessionDep
from app.schemas.player import Player
from app.services.players import PlayerService


router = APIRouter(tags=["Players"])


@router.get("/leaderboard", response_model=list[Player])
def get_leaderboard(session: SessionDep) -> list[Player]:
    return PlayerService(session).leaderboard()

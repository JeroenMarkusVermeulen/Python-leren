"""Score-endpoints, inclusief de scores die onder een speler vallen."""

from fastapi import APIRouter, status

from app.dependencies import PlayerId, SessionDep
from app.schemas.common import ErrorResponse
from app.schemas.score import Score, ScoreCreate
from app.services.scores import ScoreService


router = APIRouter(tags=["Scores"])


@router.get("/scores", response_model=list[Score])
def get_scores(session: SessionDep) -> list[Score]:
    return ScoreService(session).list_scores()


@router.get(
    "/players/{player_id}/scores", response_model=list[Score],
    responses={404: {"model": ErrorResponse}},
)
def get_player_scores(player_id: PlayerId, session: SessionDep) -> list[Score]:
    return ScoreService(session).list_player_scores(player_id)


@router.post(
    "/players/{player_id}/scores", response_model=Score,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
)
def add_score(player_id: PlayerId, data: ScoreCreate, session: SessionDep) -> Score:
    return ScoreService(session).add_score(player_id, data)

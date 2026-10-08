"""Scorelijsten blijven openbaar; punten toevoegen vereist eigenaarschap."""

from fastapi import APIRouter, status

from app.schemas.common import ErrorResponse
from app.schemas.score import Score, ScoreCreate
from app.supabase_api.dependencies import ContextDep, CurrentUserDep, PlayerId
from app.supabase_api.services.scores import ScoreService


router = APIRouter(tags=["Scores"])


@router.get("/scores", response_model=list[Score])
def get_scores(context: ContextDep) -> list[Score]:
    return ScoreService(context).list_scores()


@router.get(
    "/players/{player_id}/scores", response_model=list[Score],
    responses={404: {"model": ErrorResponse}},
)
def get_player_scores(player_id: PlayerId, context: ContextDep) -> list[Score]:
    return ScoreService(context).list_player_scores(player_id)


@router.post(
    "/players/{player_id}/scores", response_model=Score, status_code=status.HTTP_201_CREATED,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse},
               404: {"model": ErrorResponse}},
)
def add_score(
    player_id: PlayerId, data: ScoreCreate, context: ContextDep, user: CurrentUserDep,
) -> Score:
    return ScoreService(context).add_score(player_id, data, user.id)

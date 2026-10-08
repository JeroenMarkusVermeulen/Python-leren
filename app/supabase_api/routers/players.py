"""Openbaar lezen en beveiligde schrijf-acties voor spelers."""

from fastapi import APIRouter, Response, status

from app.schemas.common import ErrorResponse
from app.schemas.player import Player, PlayerCreate
from app.supabase_api.dependencies import ContextDep, CurrentUserDep, PlayerId
from app.supabase_api.services.players import PlayerService


router = APIRouter(prefix="/players", tags=["Players"])
AUTH_ERRORS = {401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}}


@router.get("", response_model=list[Player])
def get_players(context: ContextDep) -> list[Player]:
    return PlayerService(context).list_players()


@router.post(
    "", response_model=Player, status_code=status.HTTP_201_CREATED,
    responses={**AUTH_ERRORS, 400: {"model": ErrorResponse}},
)
def create_player(
    data: PlayerCreate, response: Response, context: ContextDep, user: CurrentUserDep,
) -> Player:
    player = PlayerService(context).create_player(data, user.id)
    response.headers["Location"] = f"/players/{player.id}"
    return player


@router.get("/{player_id}", response_model=Player, responses={404: {"model": ErrorResponse}})
def get_player(player_id: PlayerId, context: ContextDep) -> Player:
    return PlayerService(context).get_player(player_id)


@router.put(
    "/{player_id}", response_model=Player,
    responses={**AUTH_ERRORS, 400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_player(
    player_id: PlayerId, data: PlayerCreate, context: ContextDep, user: CurrentUserDep,
) -> Player:
    return PlayerService(context).update_player(player_id, data, user.id)


@router.delete(
    "/{player_id}", status_code=status.HTTP_204_NO_CONTENT,
    responses={**AUTH_ERRORS, 404: {"model": ErrorResponse}},
)
def delete_player(player_id: PlayerId, context: ContextDep, user: CurrentUserDep) -> None:
    PlayerService(context).delete_player(player_id, user.id)

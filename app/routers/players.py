"""Speler-CRUD: HTTP afhandelen en het werk aan de service doorgeven."""

from fastapi import APIRouter, Response, status

from app.dependencies import PlayerId, SessionDep
from app.schemas.common import ErrorResponse
from app.schemas.player import Player, PlayerCreate
from app.services.players import PlayerService


router = APIRouter(prefix="/players", tags=["Players"])


@router.get("", response_model=list[Player])
def get_players(session: SessionDep) -> list[Player]:
    return PlayerService(session).list_players()


@router.post(
    "", response_model=Player, status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
def create_player(data: PlayerCreate, response: Response, session: SessionDep) -> Player:
    player = PlayerService(session).create_player(data)
    response.headers["Location"] = f"/players/{player.id}"
    return player


@router.get(
    "/{player_id}", response_model=Player,
    responses={404: {"model": ErrorResponse}},
)
def get_player(player_id: PlayerId, session: SessionDep) -> Player:
    return PlayerService(session).get_player(player_id)


@router.put(
    "/{player_id}", response_model=Player,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def update_player(player_id: PlayerId, data: PlayerCreate, session: SessionDep) -> Player:
    return PlayerService(session).update_player(player_id, data)


@router.delete(
    "/{player_id}", status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
)
def delete_player(player_id: PlayerId, session: SessionDep) -> None:
    PlayerService(session).delete_player(player_id)

"""Speler-CRUD en eigendomscontrole naast de controles van Supabase RLS."""

from uuid import UUID

from app.schemas.player import Player, PlayerCreate
from app.services.errors import PlayerNotFoundError
from app.supabase_api.database import RequestContext
from app.supabase_api.errors import AuthorizationError
from app.supabase_api.models import PlayerRow
from app.supabase_api.repositories.players import PlayerRepository


class PlayerService:
    def __init__(self, context: RequestContext) -> None:
        self.players = PlayerRepository(context)

    def list_players(self) -> list[Player]:
        return self.players.list_with_totals()

    def get_player(self, player_id: int) -> Player:
        player = self.players.get_total(player_id)
        if player is None:
            raise PlayerNotFoundError(player_id)
        return player

    def require_owned_player(self, player_id: int, user_id: UUID) -> PlayerRow:
        row = self.players.get(player_id)
        if row is None:
            raise PlayerNotFoundError(player_id)
        if row.owner_id != user_id:
            raise AuthorizationError()
        return row

    def create_player(self, data: PlayerCreate, user_id: UUID) -> Player:
        row = self.players.add(data.username, user_id)
        return Player(id=row.id, username=row.username, score=0)

    def update_player(self, player_id: int, data: PlayerCreate, user_id: UUID) -> Player:
        self.require_owned_player(player_id, user_id)
        self.players.rename(player_id, data.username)
        return self.get_player(player_id)

    def delete_player(self, player_id: int, user_id: UUID) -> None:
        self.require_owned_player(player_id, user_id)
        self.players.delete(player_id)

    def leaderboard(self) -> list[Player]:
        return sorted(self.list_players(), key=lambda player: (-player.score, player.id))

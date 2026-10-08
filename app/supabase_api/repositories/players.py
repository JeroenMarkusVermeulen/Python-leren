"""Lees spelergegevens en totaalscores; eigendom wordt in RLS gecontroleerd."""

from uuid import UUID

from app.schemas.player import Player
from app.supabase_api.database import RequestContext
from app.supabase_api.errors import AuthorizationError, UpstreamUnavailableError
from app.supabase_api.models import PlayerRow
from app.supabase_api.repositories.queries import all_pages, execute


class PlayerRepository:
    def __init__(self, context: RequestContext) -> None:
        self.client = context.client

    def list_with_totals(self) -> list[Player]:
        rows = all_pages(lambda: self.client.table("game_player_totals")
                         .select("id,username,score").order("id"))
        return [Player.model_validate(row) for row in rows]

    def get_total(self, player_id: int) -> Player | None:
        rows = execute(self.client.table("game_player_totals")
                       .select("id,username,score").eq("id", player_id).limit(1))
        return Player.model_validate(rows[0]) if rows else None

    def get(self, player_id: int) -> PlayerRow | None:
        rows = execute(self.client.table("game_players")
                       .select("id,username,owner_id").eq("id", player_id).limit(1))
        return PlayerRow.from_record(rows[0]) if rows else None

    def add(self, username: str, owner_id: UUID) -> PlayerRow:
        rows = execute(self.client.table("game_players").insert({
            "username": username, "owner_id": str(owner_id),
        }))
        if not rows:
            raise UpstreamUnavailableError()
        return PlayerRow.from_record(rows[0])

    def rename(self, player_id: int, username: str) -> None:
        rows = execute(self.client.table("game_players")
                       .update({"username": username}).eq("id", player_id))
        if not rows:
            raise AuthorizationError()

    def delete(self, player_id: int) -> None:
        rows = execute(self.client.table("game_players").delete().eq("id", player_id))
        if not rows:
            raise AuthorizationError()

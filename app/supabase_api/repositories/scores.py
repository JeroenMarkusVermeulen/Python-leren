"""Queries voor de scorerijen in Supabase."""

from app.schemas.score import Score
from app.supabase_api.database import RequestContext
from app.supabase_api.errors import UpstreamUnavailableError
from app.supabase_api.repositories.queries import all_pages, execute


class ScoreRepository:
    def __init__(self, context: RequestContext) -> None:
        self.client = context.client

    def list_all(self) -> list[Score]:
        rows = all_pages(lambda: self.client.table("game_scores")
                         .select("id,player_id,points").order("id"))
        return [Score.model_validate(row) for row in rows]

    def list_for_player(self, player_id: int) -> list[Score]:
        rows = all_pages(lambda: self.client.table("game_scores")
                         .select("id,player_id,points").eq("player_id", player_id).order("id"))
        return [Score.model_validate(row) for row in rows]

    def add(self, player_id: int, points: int) -> Score:
        rows = execute(self.client.table("game_scores").insert({
            "player_id": player_id, "points": points,
        }))
        if not rows:
            raise UpstreamUnavailableError()
        return Score.model_validate(rows[0])

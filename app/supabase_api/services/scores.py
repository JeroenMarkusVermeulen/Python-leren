"""Iedereen kan scores lezen; alleen de speler-eigenaar kan punten toevoegen."""

from uuid import UUID

from app.schemas.score import Score, ScoreCreate
from app.supabase_api.database import RequestContext
from app.supabase_api.repositories.scores import ScoreRepository
from app.supabase_api.services.players import PlayerService


class ScoreService:
    def __init__(self, context: RequestContext) -> None:
        self.scores = ScoreRepository(context)
        self.players = PlayerService(context)

    def list_scores(self) -> list[Score]:
        return self.scores.list_all()

    def list_player_scores(self, player_id: int) -> list[Score]:
        self.players.get_player(player_id)
        return self.scores.list_for_player(player_id)

    def add_score(self, player_id: int, data: ScoreCreate, user_id: UUID) -> Score:
        self.players.require_owned_player(player_id, user_id)
        return self.scores.add(player_id, data.points)

"""Scores beheren; punten mogen alleen bij een bestaande speler horen."""

from sqlalchemy.orm import Session

from app.repositories.scores import ScoreRepository
from app.schemas.score import Score, ScoreCreate
from app.services.players import PlayerService


class ScoreService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.scores = ScoreRepository(session)
        self.players = PlayerService(session)

    def list_scores(self) -> list[Score]:
        return [Score.model_validate(row) for row in self.scores.list_all()]

    def list_player_scores(self, player_id: int) -> list[Score]:
        self.players.require_player(player_id)
        return [
            Score.model_validate(row)
            for row in self.scores.list_for_player(player_id)
        ]

    def add_score(self, player_id: int, data: ScoreCreate) -> Score:
        self.players.require_player(player_id)
        row = self.scores.add(player_id, data.points)
        self.session.commit()
        self.session.refresh(row)
        return Score.model_validate(row)

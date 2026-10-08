"""Score-queries en het optellen van de opgeslagen punten."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ScoreRow


class ScoreRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_all(self) -> list[ScoreRow]:
        return list(self.session.scalars(select(ScoreRow).order_by(ScoreRow.id)))

    def list_for_player(self, player_id: int) -> list[ScoreRow]:
        return list(self.session.scalars(
            select(ScoreRow).where(ScoreRow.player_id == player_id).order_by(ScoreRow.id)
        ))

    def total_for_player(self, player_id: int) -> int:
        return self.session.scalar(
            select(func.coalesce(func.sum(ScoreRow.points), 0)).where(
                ScoreRow.player_id == player_id
            )
        )

    def add(self, player_id: int, points: int) -> ScoreRow:
        row = ScoreRow(player_id=player_id, points=points)
        self.session.add(row)
        return row

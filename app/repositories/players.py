"""Alle queries en wijzigingen aan spelerrijen."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PlayerRow, ScoreRow


class PlayerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, player_id: int) -> PlayerRow | None:
        return self.session.get(PlayerRow, player_id)

    def list_with_totals(self) -> list[tuple[PlayerRow, int]]:
        rows = self.session.execute(
            select(PlayerRow, func.coalesce(func.sum(ScoreRow.points), 0))
            .outerjoin(ScoreRow)
            .group_by(PlayerRow.id)
            .order_by(PlayerRow.id)
        ).all()
        return [(row, total) for row, total in rows]

    def add(self, username: str, username_key: str) -> PlayerRow:
        row = PlayerRow(username=username, username_key=username_key)
        self.session.add(row)
        return row

    def rename(self, row: PlayerRow, username: str, username_key: str) -> None:
        row.username = username
        row.username_key = username_key

    def delete(self, row: PlayerRow) -> None:
        self.session.delete(row)

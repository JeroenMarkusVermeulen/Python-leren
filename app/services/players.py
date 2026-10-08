"""Spelers beheren, unieke namen bewaken en de ranglijst samenstellen."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import PlayerRow
from app.repositories.players import PlayerRepository
from app.repositories.scores import ScoreRepository
from app.schemas.player import Player, PlayerCreate
from app.services.errors import DuplicateUsernameError, PlayerNotFoundError


class PlayerService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.players = PlayerRepository(session)
        self.scores = ScoreRepository(session)

    def require_player(self, player_id: int) -> PlayerRow:
        row = self.players.get(player_id)
        if row is None:
            raise PlayerNotFoundError(player_id)
        return row

    def list_players(self) -> list[Player]:
        return [
            Player(id=row.id, username=row.username, score=total)
            for row, total in self.players.list_with_totals()
        ]

    def get_player(self, player_id: int) -> Player:
        row = self.require_player(player_id)
        return Player(
            id=row.id, username=row.username,
            score=self.scores.total_for_player(player_id),
        )

    def create_player(self, data: PlayerCreate) -> Player:
        row = self.players.add(data.username, data.username.casefold())
        self._commit_unique_username()
        self.session.refresh(row)
        return Player(id=row.id, username=row.username, score=0)

    def update_player(self, player_id: int, data: PlayerCreate) -> Player:
        row = self.require_player(player_id)
        self.players.rename(row, data.username, data.username.casefold())
        self._commit_unique_username()
        return self.get_player(player_id)

    def delete_player(self, player_id: int) -> None:
        row = self.require_player(player_id)
        self.players.delete(row)
        self.session.commit()

    def leaderboard(self) -> list[Player]:
        return sorted(self.list_players(), key=lambda player: (-player.score, player.id))

    def _commit_unique_username(self) -> None:
        try:
            self.session.commit()
        except IntegrityError as exc:
            self.session.rollback()
            raise DuplicateUsernameError() from exc

"""SQLAlchemy-model voor de tabel scores en de relatie met een speler."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.player import PlayerRow


class ScoreRow(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    player: Mapped["PlayerRow"] = relationship(back_populates="scores")

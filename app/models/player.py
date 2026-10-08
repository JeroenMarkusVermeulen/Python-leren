"""SQLAlchemy-model voor de tabel players; bevat geen HTTP-validatie."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.score import ScoreRow


class PlayerRow(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    username_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    scores: Mapped[list["ScoreRow"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )

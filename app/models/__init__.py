"""Importeer beide models zodat SQLAlchemy hun tabellen en relaties kent."""

from app.models.base import Base
from app.models.player import PlayerRow
from app.models.score import ScoreRow

__all__ = ["Base", "PlayerRow", "ScoreRow"]

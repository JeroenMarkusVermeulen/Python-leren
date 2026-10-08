"""SQLite-verbindingen, sessies en het eenmalig vullen van een nieuwe database."""

from pathlib import Path

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

from app.models import Base, PlayerRow, ScoreRow


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "game_scores.db"


class Database:
    def __init__(self, db_path: Path | None = None) -> None:
        self.path = (db_path or DEFAULT_DB_PATH).resolve()
        self.engine = create_engine(
            f"sqlite:///{self.path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        self.session_factory = sessionmaker(bind=self.engine)

    @staticmethod
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    def initialize(self) -> None:
        new_database = not inspect(self.engine).has_table("players")
        Base.metadata.create_all(self.engine)
        if new_database:
            with self.session_factory.begin() as session:
                alice = PlayerRow(username="Alice", username_key="alice")
                bob = PlayerRow(username="Bob", username_key="bob")
                alice.scores.append(ScoreRow(points=100))
                bob.scores.append(ScoreRow(points=150))
                session.add_all([alice, bob])

    def close(self) -> None:
        self.engine.dispose()

"""Sprint 4: Game Score API met permanente opslag in SQLite.

Start met ``python sprint4.py`` en open http://127.0.0.1:8000/docs.
De database staat standaard naast dit bestand als ``game_scores.db``.
"""

from collections.abc import Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path as ApiPath, Response, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator
from sqlalchemy import ForeignKey, Integer, String, create_engine, event, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class PlayerRow(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    username_key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    scores: Mapped[list["ScoreRow"]] = relationship(
        back_populates="player", cascade="all, delete-orphan"
    )


class ScoreRow(Base):
    __tablename__ = "scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"), nullable=False, index=True
    )
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    player: Mapped[PlayerRow] = relationship(back_populates="scores")


class ApiStatus(BaseModel):
    message: str


class PlayerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50, examples=["Charlie"])

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Gebruikersnaam mag niet leeg zijn.")
        if len(value) > 50:
            raise ValueError("Gebruikersnaam mag maximaal 50 tekens bevatten.")
        return value


class ScoreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: StrictInt = Field(gt=0, examples=[25])


class Player(BaseModel):
    id: int
    username: str
    score: int


class Score(BaseModel):
    id: int
    player_id: int
    points: int


class ErrorResponse(BaseModel):
    detail: str


def player_response(row: PlayerRow, total: int) -> Player:
    return Player(id=row.id, username=row.username, score=total)


def find_player(session: Session, player_id: int) -> PlayerRow:
    row = session.get(PlayerRow, player_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Speler met ID {player_id} is niet gevonden.",
        )
    return row


def total_score(session: Session, player_id: int) -> int:
    return session.scalar(
        select(func.coalesce(func.sum(ScoreRow.points), 0)).where(
            ScoreRow.player_id == player_id
        )
    )


def player_list(session: Session) -> list[Player]:
    rows = session.execute(
        select(PlayerRow, func.coalesce(func.sum(ScoreRow.points), 0))
        .outerjoin(ScoreRow)
        .group_by(PlayerRow.id)
        .order_by(PlayerRow.id)
    ).all()
    return [player_response(row, total) for row, total in rows]


def create_app(db_path: Path | None = None) -> FastAPI:
    """Maak een API met een eigen databasebestand, ook bruikbaar in tests."""

    database_file = (db_path or Path(__file__).with_name("game_scores.db")).resolve()
    engine = create_engine(
        f"sqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    session_factory = sessionmaker(bind=engine)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # Voor een nieuwe database komen de twee voorbeeldspelers uit Sprint 2 terug.
        from sqlalchemy import inspect

        new_database = not inspect(engine).has_table("players")
        Base.metadata.create_all(engine)
        if new_database:
            with session_factory.begin() as session:
                alice = PlayerRow(username="Alice", username_key="alice")
                bob = PlayerRow(username="Bob", username_key="bob")
                alice.scores.append(ScoreRow(points=100))
                bob.scores.append(ScoreRow(points=150))
                session.add_all([alice, bob])
        yield
        engine.dispose()

    app = FastAPI(
        title="Game Score API - Sprint 4",
        description="Spelers en scores worden permanent opgeslagen in SQLite.",
        version="4.0.0",
        lifespan=lifespan,
    )

    def get_session() -> Iterator[Session]:
        with session_factory() as session:
            yield session

    SessionDep = Annotated[Session, Depends(get_session)]
    PlayerId = Annotated[int, ApiPath(ge=1)]

    @app.get("/", response_model=ApiStatus, tags=["Algemeen"])
    def read_root() -> ApiStatus:
        return ApiStatus(message="De Players API werkt!")

    @app.get("/players", response_model=list[Player], tags=["Players"])
    def get_players(session: SessionDep) -> list[Player]:
        return player_list(session)

    @app.post(
        "/players",
        response_model=Player,
        status_code=status.HTTP_201_CREATED,
        responses={400: {"model": ErrorResponse}},
        tags=["Players"],
    )
    def create_player(data: PlayerCreate, response: Response, session: SessionDep) -> Player:
        row = PlayerRow(username=data.username, username_key=data.username.casefold())
        session.add(row)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=400, detail="Deze gebruikersnaam bestaat al.")
        session.refresh(row)
        response.headers["Location"] = f"/players/{row.id}"
        return player_response(row, 0)

    @app.get(
        "/players/{player_id}",
        response_model=Player,
        responses={404: {"model": ErrorResponse}},
        tags=["Players"],
    )
    def get_player(player_id: PlayerId, session: SessionDep) -> Player:
        row = find_player(session, player_id)
        return player_response(row, total_score(session, player_id))

    @app.put(
        "/players/{player_id}",
        response_model=Player,
        responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
        tags=["Players"],
    )
    def update_player(player_id: PlayerId, data: PlayerCreate, session: SessionDep) -> Player:
        row = find_player(session, player_id)
        row.username = data.username
        row.username_key = data.username.casefold()
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            raise HTTPException(status_code=400, detail="Deze gebruikersnaam bestaat al.")
        return player_response(row, total_score(session, player_id))

    @app.delete(
        "/players/{player_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        responses={404: {"model": ErrorResponse}},
        tags=["Players"],
    )
    def delete_player(player_id: PlayerId, session: SessionDep) -> None:
        row = find_player(session, player_id)
        session.delete(row)
        session.commit()

    @app.get("/scores", response_model=list[Score], tags=["Scores"])
    def get_scores(session: SessionDep) -> list[ScoreRow]:
        return session.scalars(select(ScoreRow).order_by(ScoreRow.id)).all()

    @app.get(
        "/players/{player_id}/scores",
        response_model=list[Score],
        responses={404: {"model": ErrorResponse}},
        tags=["Scores"],
    )
    def get_player_scores(player_id: PlayerId, session: SessionDep) -> list[ScoreRow]:
        find_player(session, player_id)
        return session.scalars(
            select(ScoreRow).where(ScoreRow.player_id == player_id).order_by(ScoreRow.id)
        ).all()

    @app.post(
        "/players/{player_id}/scores",
        response_model=Score,
        status_code=status.HTTP_201_CREATED,
        responses={404: {"model": ErrorResponse}},
        tags=["Scores"],
    )
    def add_score(player_id: PlayerId, data: ScoreCreate, session: SessionDep) -> ScoreRow:
        find_player(session, player_id)
        row = ScoreRow(player_id=player_id, points=data.points)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row

    @app.get("/leaderboard", response_model=list[Player], tags=["Players"])
    def get_leaderboard(session: SessionDep) -> list[Player]:
        return sorted(player_list(session), key=lambda player: (-player.score, player.id))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sprint4:app", host="127.0.0.1", port=8000)

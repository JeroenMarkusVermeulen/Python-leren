"""Sprint 3: REST API voor spelers en hun scores.

Start met ``python sprint3.py`` en open http://127.0.0.1:8000/docs.
De gegevens staan in het geheugen en worden bij een herstart teruggezet.
"""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, Response, status
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator


class ApiStatus(BaseModel):
    message: str


class PlayerCreate(BaseModel):
    """Gegevens die nodig zijn om een speler aan te maken of te vervangen."""

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


class Player(BaseModel):
    id: int
    username: str
    score: int


class ScoreCreate(BaseModel):
    """Een positieve hoeveelheid punten om aan een speler toe te voegen."""

    model_config = ConfigDict(extra="forbid")

    points: StrictInt = Field(gt=0, examples=[25])


class Score(BaseModel):
    id: int
    player_id: int
    points: int


class ErrorResponse(BaseModel):
    detail: str


players: list[Player] = [
    Player(id=1, username="Alice", score=100),
    Player(id=2, username="Bob", score=150),
]
scores: list[Score] = [
    Score(id=1, player_id=1, points=100),
    Score(id=2, player_id=2, points=150),
]
next_player_id = 3
next_score_id = 3


def find_player(player_id: int) -> Player:
    for player in players:
        if player.id == player_id:
            return player
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Speler met ID {player_id} is niet gevonden.",
    )


def check_username(username: str, current_id: int | None = None) -> None:
    if any(
        player.username.casefold() == username.casefold() and player.id != current_id
        for player in players
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Deze gebruikersnaam bestaat al.",
        )


app = FastAPI(
    title="Game Score API - Sprint 3",
    description="Beheer spelers en voeg scores toe. Gegevens staan tijdelijk in het geheugen.",
    version="3.0.0",
)


@app.get("/", response_model=ApiStatus, tags=["Algemeen"])
def read_root() -> ApiStatus:
    return ApiStatus(message="De Players API werkt!")


@app.get("/players", response_model=list[Player], tags=["Players"])
def get_players() -> list[Player]:
    return players


@app.post(
    "/players",
    response_model=Player,
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse, "description": "Gebruikersnaam bestaat al."}},
    tags=["Players"],
)
def create_player(data: PlayerCreate, response: Response) -> Player:
    global next_player_id
    check_username(data.username)
    player = Player(id=next_player_id, username=data.username, score=0)
    next_player_id += 1
    players.append(player)
    response.headers["Location"] = f"/players/{player.id}"
    return player


@app.get(
    "/players/{player_id}",
    response_model=Player,
    responses={404: {"model": ErrorResponse}},
    tags=["Players"],
)
def get_player(player_id: Annotated[int, Path(ge=1)]) -> Player:
    return find_player(player_id)


@app.put(
    "/players/{player_id}",
    response_model=Player,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    tags=["Players"],
)
def update_player(player_id: Annotated[int, Path(ge=1)], data: PlayerCreate) -> Player:
    player = find_player(player_id)
    check_username(data.username, current_id=player_id)
    player.username = data.username
    return player


@app.delete(
    "/players/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": ErrorResponse}},
    tags=["Players"],
)
def delete_player(player_id: Annotated[int, Path(ge=1)]) -> None:
    player = find_player(player_id)
    players.remove(player)
    scores[:] = [score for score in scores if score.player_id != player_id]


@app.get("/scores", response_model=list[Score], tags=["Scores"])
def get_scores() -> list[Score]:
    return scores


@app.get(
    "/players/{player_id}/scores",
    response_model=list[Score],
    responses={404: {"model": ErrorResponse}},
    tags=["Scores"],
)
def get_player_scores(player_id: Annotated[int, Path(ge=1)]) -> list[Score]:
    find_player(player_id)
    return [score for score in scores if score.player_id == player_id]


@app.post(
    "/players/{player_id}/scores",
    response_model=Score,
    status_code=status.HTTP_201_CREATED,
    responses={404: {"model": ErrorResponse}},
    tags=["Scores"],
)
def add_score(player_id: Annotated[int, Path(ge=1)], data: ScoreCreate) -> Score:
    global next_score_id
    player = find_player(player_id)
    score = Score(id=next_score_id, player_id=player_id, points=data.points)
    next_score_id += 1
    scores.append(score)
    player.score += data.points
    return score


@app.get("/leaderboard", response_model=list[Player], tags=["Players"])
def get_leaderboard() -> list[Player]:
    return sorted(players, key=lambda player: (-player.score, player.id))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sprint3:app", host="127.0.0.1", port=8000, reload=True)

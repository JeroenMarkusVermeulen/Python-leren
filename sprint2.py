"""Sprint 2: een eenvoudige spelers-API met FastAPI.

FastAPI is een modern Python-framework voor het bouwen van web-API's. Het
controleert gegevens met type hints en maakt automatisch interactieve
documentatie. Na het starten staat Swagger UI op http://127.0.0.1:8000/docs.

HTTP in het kort:
- Een request is de aanvraag van een client aan de server, bijvoorbeeld GET /.
- Een response is het antwoord van de server, met data en een statuscode.
- Statuscodes vatten het resultaat samen: 200 betekent gelukt, 404 betekent
  dat iets niet gevonden is en 422 betekent dat invoer ongeldig is.

Start de server met: python sprint2.py
"""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Path, status
from pydantic import BaseModel


class ApiStatus(BaseModel):
    """Het JSON-model voor het test-endpoint."""

    message: str


class Player(BaseModel):
    """Een speler zoals die in de JSON-responses wordt weergegeven."""

    id: int
    username: str
    score: int


class ErrorResponse(BaseModel):
    """De vorm van een foutresponse."""

    detail: str


# De spelers uit Sprint 1. Pydantic zet deze objecten automatisch om naar JSON.
players: list[Player] = [
    Player(id=1, username="Alice", score=100),
    Player(id=2, username="Bob", score=150),
]


app = FastAPI(
    title="Sprint 2 Players API",
    description=(
        "Een oefen-API voor het ophalen van spelers en een gesorteerd "
        "leaderboard. Probeer de endpoints met 'Try it out'."
    ),
    version="1.0.0",
)


@app.get(
    "/",
    response_model=ApiStatus,
    status_code=status.HTTP_200_OK,
    summary="Controleer of de API werkt",
)
def read_root() -> ApiStatus:
    """Geef een eenvoudig JSON-antwoord terug om de API te testen."""

    return ApiStatus(message="De Players API werkt!")


@app.get(
    "/players",
    response_model=list[Player],
    status_code=status.HTTP_200_OK,
    summary="Haal alle spelers op",
)
def get_players() -> list[Player]:
    """Geef alle spelers als een JSON-array terug."""

    return players


@app.get(
    "/players/{id}",
    response_model=Player,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": "De speler bestaat niet.",
        }
    },
    summary="Haal één speler op",
)
def get_player(
    id: Annotated[int, Path(ge=1, description="Het unieke ID van de speler")],
) -> Player:
    """Zoek een speler op ID of geef een duidelijke 404-response terug."""

    for player in players:
        if player.id == id:
            return player

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Speler met ID {id} is niet gevonden.",
    )


@app.get(
    "/leaderboard",
    response_model=list[Player],
    status_code=status.HTTP_200_OK,
    summary="Haal het leaderboard op",
)
def get_leaderboard() -> list[Player]:
    """Geef spelers terug van hoogste naar laagste score."""

    return sorted(players, key=lambda player: (-player.score, player.id))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sprint2:app", host="127.0.0.1", port=8000, reload=True)

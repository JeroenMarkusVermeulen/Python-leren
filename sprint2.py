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

from fastapi import FastAPI, status
from pydantic import BaseModel


class ApiStatus(BaseModel):
    """Het JSON-model voor het test-endpoint."""

    message: str


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("sprint2:app", host="127.0.0.1", port=8000, reload=True)

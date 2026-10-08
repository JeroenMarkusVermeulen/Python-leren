"""Vertaal businessfouten centraal naar de bestaande HTTP-antwoorden."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.services.errors import DuplicateUsernameError, PlayerNotFoundError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(PlayerNotFoundError)
    async def player_not_found(_request: Request, exc: PlayerNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
        )

    @app.exception_handler(DuplicateUsernameError)
    async def duplicate_username(_request: Request, exc: DuplicateUsernameError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
        )

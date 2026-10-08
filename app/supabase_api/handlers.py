"""Gebruik geschikte statuscodes en neem geen ingevoerde secrets in fouten op."""

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.handlers import register_error_handlers as register_player_errors
from app.supabase_api.errors import (
    AuthenticationError, AuthorizationError, RateLimitError,
    RegistrationError, UpstreamUnavailableError,
)


def register_error_handlers(app: FastAPI) -> None:
    register_player_errors(app)
    codes = {
        AuthenticationError: 401, AuthorizationError: 403, RegistrationError: 400,
        RateLimitError: 429, UpstreamUnavailableError: 503,
    }

    async def business_error(_request: Request, exc: Exception) -> JSONResponse:
        code = codes[type(exc)]
        headers = {"WWW-Authenticate": "Bearer"} if code == 401 else {}
        if code == 429:
            headers["Retry-After"] = "60"
        return JSONResponse(status_code=code, content={"detail": str(exc)}, headers=headers)

    for error_type in codes:
        app.add_exception_handler(error_type, business_error)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_request: Request, exc: RequestValidationError) -> JSONResponse:
        # Pydantic kan anders het ruwe password in het veld 'input' terugsturen.
        errors = [{key: error[key] for key in ("type", "loc", "msg")} for error in exc.errors()]
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(httpx.HTTPError)
    async def network_error(_request: Request, _exc: httpx.HTTPError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(UpstreamUnavailableError())})

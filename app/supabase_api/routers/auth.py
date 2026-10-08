"""Registreren en inloggen via Supabase Auth; Swagger accepteert het bearer-token."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.common import ErrorResponse
from app.supabase_api.dependencies import ContextDep, CurrentUserDep
from app.supabase_api.schemas import (
    AuthUser, RefreshRequest, RegisterRequest, RegistrationResult, Token,
)
from app.supabase_api.services.auth import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


def prevent_caching(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"


@router.post(
    "/register", response_model=RegistrationResult, status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}, 429: {"model": ErrorResponse}},
)
def register(data: RegisterRequest, response: Response, context: ContextDep) -> RegistrationResult:
    prevent_caching(response)
    return AuthService(context).register(data)


@router.post("/login", response_model=Token, responses={401: {"model": ErrorResponse}})
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response, context: ContextDep,
) -> Token:
    prevent_caching(response)
    # Het OAuth-formulierveld 'username' bevat hier het e-mailadres.
    return AuthService(context).login(form.username, form.password)


@router.get("/me", response_model=AuthUser, responses={401: {"model": ErrorResponse}})
def me(user: CurrentUserDep, response: Response) -> AuthUser:
    prevent_caching(response)
    return user


@router.post("/refresh", response_model=Token, responses={401: {"model": ErrorResponse}})
def refresh(data: RefreshRequest, response: Response, context: ContextDep) -> Token:
    prevent_caching(response)
    return AuthService(context).refresh(data.refresh_token.get_secret_value())

"""Iedere request krijgt een eigen client; beveiligde routes valideren het token."""

from collections.abc import Iterator
from typing import Annotated

import httpx
from fastapi import Depends, Path, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param

from app.supabase_api.database import RequestContext, create_context
from app.supabase_api.schemas import AuthUser
from app.supabase_api.services.auth import AuthService


bearer = HTTPBearer(auto_error=False)


def get_context(request: Request) -> Iterator[RequestContext]:
    scheme, value = get_authorization_scheme_param(request.headers.get("Authorization"))
    token = value if scheme.lower() == "bearer" else None
    with httpx.Client(timeout=15, transport=request.app.state.http_transport) as http_client:
        yield create_context(request.app.state.settings, http_client, token)


ContextDep = Annotated[RequestContext, Depends(get_context)]
PlayerId = Annotated[int, Path(ge=1)]


def get_current_user(
    context: ContextDep,
    _credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthUser:
    return AuthService(context).current_user()


CurrentUserDep = Annotated[AuthUser, Depends(get_current_user)]

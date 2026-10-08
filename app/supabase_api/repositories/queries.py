"""Vertaal bekende Postgres-fouten en lees lijsten in begrensde pagina's."""

from postgrest.exceptions import APIError

from app.services.errors import DuplicateUsernameError
from app.supabase_api.errors import AuthorizationError, UpstreamUnavailableError


PAGE_SIZE = 500


def execute(query) -> list[dict]:
    try:
        return query.execute().data or []
    except APIError as exc:
        if exc.code == "23505":
            raise DuplicateUsernameError() from exc
        if exc.code == "42501":
            raise AuthorizationError() from exc
        raise UpstreamUnavailableError() from exc


def all_pages(query_factory) -> list[dict]:
    rows = []
    while True:
        start = len(rows)
        page = execute(query_factory().range(start, start + PAGE_SIZE - 1))
        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows

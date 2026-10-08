"""Maak per request een Supabase-client; de gebruiker bepaalt de RLS-context."""

from dataclasses import dataclass

import httpx
from supabase import Client, ClientOptions, create_client

from app.supabase_api.config import Settings


@dataclass
class RequestContext:
    client: Client
    access_token: str | None


def create_context(settings: Settings, http_client: httpx.Client, token: str | None) -> RequestContext:
    client = create_client(
        settings.supabase_url,
        settings.supabase_publishable_key,
        options=ClientOptions(
            persist_session=False,
            auto_refresh_token=False,
            httpx_client=http_client,
        ),
    )
    if token:
        client.postgrest.auth(token)
    return RequestContext(client=client, access_token=token)

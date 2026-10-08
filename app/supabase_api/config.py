"""Lees de Supabase-projectinstellingen; gebruik uitsluitend een publieke API-key."""

import base64
import json
import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    supabase_url: str = ""
    supabase_publishable_key: str = ""

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
        return cls(
            supabase_url=os.getenv("SUPABASE_URL", "").rstrip("/"),
            supabase_publishable_key=os.getenv("SUPABASE_PUBLISHABLE_KEY", ""),
        )

    def validate(self) -> None:
        url = urlsplit(self.supabase_url)
        local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        if (
            not url.hostname or url.username or url.password or url.query or url.fragment
            or url.path not in {"", "/"}
            or (url.scheme != "https" and not (local and url.scheme == "http"))
        ):
            raise ValueError("Vul een geldige SUPABASE_URL in .env in.")
        key = self.supabase_publishable_key
        if key.startswith("sb_publishable_"):
            return
        # Een oude anon-key mag ook; een service-role-key zou RLS omzeilen.
        try:
            payload = key.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            if isinstance(claims, dict) and claims.get("role") == "anon":
                return
        except (IndexError, ValueError, UnicodeError):
            pass
        raise ValueError("Gebruik SUPABASE_PUBLISHABLE_KEY, geen secret- of service-role-key.")

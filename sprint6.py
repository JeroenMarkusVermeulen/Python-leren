"""Start Sprint 6 vanuit Python leren; Supabase-instellingen staan in .env."""

from app.supabase_api.main import app, create_app

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.supabase_api.main:app", host="127.0.0.1", port=8000)

"""Start Sprint 5 met python sprint5.py vanuit de projectmap."""

from app.main import app, create_app

__all__ = ["app", "create_app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000)

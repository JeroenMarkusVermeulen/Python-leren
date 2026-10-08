"""FastAPI geeft ieder request een eigen, automatisch gesloten databasesessie."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Path, Request
from sqlalchemy.orm import Session


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.database.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
PlayerId = Annotated[int, Path(ge=1)]

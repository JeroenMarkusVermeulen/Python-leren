"""Python-weergave van een databaserij; de tabeldefinities staan in de SQL-migratie."""

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PlayerRow:
    id: int
    username: str
    owner_id: UUID | None

    @classmethod
    def from_record(cls, record: dict) -> "PlayerRow":
        return cls(
            id=record["id"], username=record["username"],
            owner_id=UUID(record["owner_id"]) if record.get("owner_id") else None,
        )

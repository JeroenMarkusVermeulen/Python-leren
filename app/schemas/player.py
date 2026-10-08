"""Spelerinvoer en openbare spelergegevens, los van de databasekolommen."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlayerCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1, max_length=50, examples=["Charlie"])

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Gebruikersnaam mag niet leeg zijn.")
        if len(value) > 50:
            raise ValueError("Gebruikersnaam mag maximaal 50 tekens bevatten.")
        return value


class Player(BaseModel):
    id: int
    username: str
    score: int

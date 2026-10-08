"""Score-invoer accepteert uitsluitend positieve gehele getallen."""

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class ScoreCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    points: StrictInt = Field(gt=0, examples=[25])


class Score(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    points: int

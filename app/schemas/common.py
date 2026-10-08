"""Antwoorden die niet bij een afzonderlijke resource horen."""

from pydantic import BaseModel


class ApiStatus(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str

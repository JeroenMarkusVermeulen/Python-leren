"""Algemene beschikbaarheidscontrole."""

from fastapi import APIRouter

from app.schemas.common import ApiStatus


router = APIRouter(tags=["Algemeen"])


@router.get("/", response_model=ApiStatus)
def read_root() -> ApiStatus:
    return ApiStatus(message="De Players API werkt!")

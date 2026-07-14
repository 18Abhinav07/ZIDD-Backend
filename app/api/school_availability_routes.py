"""Minimal School surface mounted when the product is disabled."""

from fastapi import APIRouter

from app.services.school.authority import school_route_owner
from app.services.school.availability import (
    school_availability,
    unavailable_school_state,
)


router = APIRouter(prefix="/school", tags=["school-availability"])


@router.get("/state")
@school_route_owner("app.services.school.availability")
async def school_availability_state() -> dict:
    return unavailable_school_state(school_availability())


__all__ = ["router"]

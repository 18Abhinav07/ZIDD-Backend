"""Explicit retirement responses for every previously mounted School API."""

from fastapi import APIRouter, HTTPException

from app.services.school.authority import (
    RETIRED_SCHOOL_ENDPOINT_SPECS,
    school_route_owner,
)


router = APIRouter(tags=["school-retired"])


def _retired_endpoint(endpoint_name: str):
    async def retired_school_endpoint() -> None:
        raise HTTPException(
            status_code=410,
            detail={
                "code": "school_endpoint_retired",
                "replacement": "/school/state",
            },
        )

    retired_school_endpoint.__name__ = endpoint_name
    return school_route_owner("app.api.school_retirement_routes")(
        retired_school_endpoint
    )


for _method, _path, _endpoint_name in RETIRED_SCHOOL_ENDPOINT_SPECS:
    router.add_api_route(
        _path,
        _retired_endpoint(_endpoint_name),
        methods=[_method],
        include_in_schema=False,
    )


__all__ = ["router"]

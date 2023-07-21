from fastapi import APIRouter, Response
from pydantic import BaseModel

from api.endpoints.schemas import School, SchoolsResponse

schools_router = APIRouter(prefix="/schools", tags=[""])


@schools_router.get("/")
async def schools() -> SchoolsResponse:
    return SchoolsResponse(
        schools=[School(id="001", title="Bellevue College", shortName="BC")]
    )

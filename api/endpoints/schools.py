from fastapi import APIRouter, Response
from pydantic import BaseModel

schools_router = APIRouter(prefix='/schools', tags=[""])

class School(BaseModel):
    id: str
    title: str
    shortName: str

class SchoolsResponse(BaseModel):
    schools: list[School] = []

@schools_router.get('/')
async def schools() -> SchoolsResponse:
    return SchoolsResponse(schools = [School(id="001", title="Bellevue College", shortName="BC")])

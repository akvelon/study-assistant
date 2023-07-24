"""
    List of schools endpoint
"""

from fastapi import APIRouter
from api.db.schools import schools_db

from api.endpoints.schemas import School, SchoolsResponse

schools_router = APIRouter(prefix="/schools", tags=[""])


@schools_router.get("/")
async def schools() -> SchoolsResponse:
    """Returns a list of all the stored schools"""
    schools_get = schools_db.get_schools()
    schools_list = []
    for row in schools_get:
        id_value, title, short_name = row
        schools_list.append(School(id=id_value, title=title, shortName=short_name))

    return SchoolsResponse(schools=schools_list)

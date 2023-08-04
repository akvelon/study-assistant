"""School update endpoint"""
from fastapi import Depends
from pydantic import BaseModel
from typing_extensions import Annotated

from api.endpoints.user import user_router, User, get_current_user
from api.db.users import users_db


class UpdateSchoolRequest(BaseModel):
    """Update school request entry"""

    schoolId: int


class UpdateSchoolResponse(User):
    """Update school response entry"""


@user_router.post("/school")
async def set_school_id(
    req: UpdateSchoolRequest, user: Annotated[str, Depends(get_current_user)]
) -> UpdateSchoolResponse:
    """Update school for given user"""
    users_db.change_school_id(user, req.schoolId)
    return UpdateSchoolResponse(id=0, email="", schoolId=req.schoolId)

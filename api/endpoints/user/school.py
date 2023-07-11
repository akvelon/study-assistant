import sqlite3
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing_extensions import Annotated
import os

from api.endpoints.user import user_router, User, get_current_user

class UpdateSchoolRequest(BaseModel):
    schoolId: int

class UpdateSchoolResponse(User):
    pass

# TODO: not implemented, should update user entry using UsersDB class with the new school id
@user_router.post("/school")
async def set_school_id(req: UpdateSchoolRequest, user: Annotated[str, Depends(get_current_user)]) -> UpdateSchoolResponse:
    return UpdateIDResponse('', req.schoolId)
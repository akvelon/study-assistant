from fastapi import APIRouter, Response, Depends, HTTPException
from pydantic import BaseModel
from typing import Annotated
from settings import settings

from api.endpoints.schemas import Message, HistoryResponse
from api.endpoints.user import User, get_current_user
from api.db.history import history_db, HistoryDbException, InvalidUserIdException

history_router = APIRouter(prefix="/history", tags=[""])


@history_router.get("/")
async def get_history_from_user_id(
    user: Annotated[str, Depends(get_current_user)]
) -> HistoryResponse:
    try:
        history = history_db.get_all_history_by_user_id(user.id)
        return HistoryResponse(history=history)
    except InvalidUserIdException as e:
        raise HTTPException(status_code=404, detail="User not found")
    except HistoryDbException as e:
        # Server DB error
        raise HTTPException(status_code=500)

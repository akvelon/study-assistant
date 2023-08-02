"""
    History endpoint
"""
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from fastapi_pagination import Page, paginate

from api.endpoints.schemas import HistoryResponse, History
from api.endpoints.user import get_current_user
from api.db.history import history_db, HistoryDbException, InvalidUserIdException

history_router = APIRouter(prefix="/history", tags=[""])


@history_router.get("/")
async def get_history_from_user_id(
    user: Annotated[str, Depends(get_current_user)],
) -> HistoryResponse:
    """Returns a list of user's history"""
    try:
        history = history_db.get_all_history_by_user_id(user.id)
        return HistoryResponse(history=history)
    except InvalidUserIdException as error:
        raise HTTPException(status_code=404, detail="User not found") from error
    except HistoryDbException as error:
        # Server DB error
        raise HTTPException(status_code=500) from error


Page = Page.with_custom_options(
    size=Field(20, ge=1, le=500),
)


@history_router.get("/paged")
async def get_history_from_user_id_paged(
    user: Annotated[str, Depends(get_current_user)],
) -> Page[History]:
    """Returns a paginated list of user's history"""
    try:
        history = history_db.get_all_history_by_user_id(user.id)
        return paginate(history)
    except InvalidUserIdException as error:
        raise HTTPException(status_code=404, detail="User not found") from error
    except HistoryDbException as error:
        # Server DB error
        raise HTTPException(status_code=500) from error

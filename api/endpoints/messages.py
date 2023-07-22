"""Messages endpoint"""
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated

from api.endpoints.schemas import MessagesRequest, MessagesResponse
from api.assistants.study_assistant import StudyAssistant, UsersMessageMissingException
from api.assistants.history.manager import UnauthorizedUserEditingHistoryException
from api.db.history import InvalidHistoryException, InvalidChatIdException
from api.endpoints.user import get_current_user_optional

assistant = StudyAssistant()
messages_router = APIRouter(prefix="/messages", tags=[""])


@messages_router.post("/", response_model_exclude_none=True)
async def messages(
    request: MessagesRequest,
    user: Annotated[str, Depends(get_current_user_optional)],
) -> MessagesResponse:
    """Takes list of messages and returns response from assistant."""
    try:
        # Excluding prompt, request.messages must be odd length
        # because assistant has not responded yet.
        if (len(request.messages) % 2) == 0:
            raise UsersMessageMissingException

        # Pass request to assistant, assuming last message is user's
        assistant_response = await assistant.generate_response(request, user)

        return MessagesResponse(
            chat=assistant_response.chat,
            messages=assistant_response.messages,
            quickReplies=assistant_response.quickReplies,
        )
    except UsersMessageMissingException as ex:
        raise HTTPException(
            status_code=400, detail=str("User's message missing.")
        ) from ex
    except InvalidHistoryException as ex:
        raise HTTPException(status_code=404, detail=str("Invalid history_id.")) from ex
    except InvalidChatIdException as ex:
        raise HTTPException(
            status_code=404, detail=str("Invalid chat id or not found.")
        ) from ex
    except UnauthorizedUserEditingHistoryException as ex:
        raise HTTPException(
            status_code=403, detail=str("Unauthorized user editing history")
        ) from ex
    except Exception as ex:
        # Safeguard server from crashing.
        print(ex)
        raise HTTPException(status_code=500, detail=str("Internal server error")) from ex

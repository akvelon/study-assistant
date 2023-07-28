"""Messages endpoint"""
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from typing_extensions import Annotated

from api.assistants.history.manager import UnauthorizedUserEditingHistoryException
from api.assistants.study_assistant import StudyAssistant, UsersMessageMissingException
from api.db.history import InvalidChatIdException, InvalidHistoryException
from api.endpoints.schemas import MessagesRequest, MessagesResponse
from api.endpoints.user import get_current_user_optional

assistant = StudyAssistant()
messages_router = APIRouter(prefix="/messages", tags=[""])


@messages_router.post("/", response_model_exclude_none=True)
async def messages(
    request: MessagesRequest,
    user: Annotated[str, Depends(get_current_user_optional)],
) -> MessagesResponse:
    """Takes list of messages or audio file and returns response from assistant."""
    try:
        # Excluding prompt, request.messages must be odd length
        # because assistant has not responded yet.
        if (len(request.messages) % 2) == 0:
            raise UsersMessageMissingException

        school_id = user.schoolId if user and user.schoolId else None

        return await assistant.generate_response(request, user, school_id)
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


@messages_router.post("/audio", response_model_exclude_none=True)
async def messages_audio(
    audio_file: UploadFile,
    user: Annotated[str, Depends(get_current_user_optional)],
    chat_id: Annotated[int, Form()] | None = Form(None),
) -> MessagesResponse:
    """Takes audio file and returns response from assistant."""

    if audio_file.content_type != "audio/mpeg":
        raise HTTPException(status_code=400, detail=str("Invalid audio type."))

    try:
        school_id = user.schoolId if user and user.schoolId else None

        return await assistant.generate_response_audio(
            audio_file, chat_id, user, school_id
        )
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

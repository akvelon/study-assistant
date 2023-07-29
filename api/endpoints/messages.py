"""Messages endpoint"""

import time

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile
from typing_extensions import Annotated

from api.endpoints.schemas import MessagesRequest, MessagesResponse
from api.assistants.study_assistant.study_assistant import (
    StudyAssistant,
    UsersMessageMissingException,
)
from api.assistants.history.manager import UnauthorizedUserEditingHistoryException
from api.assistants.quick_replies.quick_replies import generate_quick_replies
from api.db.history import InvalidHistoryException, InvalidChatIdException
from api.endpoints.user import get_current_user_optional

assistant = StudyAssistant()
messages_router = APIRouter(prefix="/messages", tags=[""])


@messages_router.post("/", response_model_exclude_none=True)
async def messages(
    request: MessagesRequest,
    user: Annotated[str, Depends(get_current_user_optional)],
) -> MessagesResponse:
    """Takes list of messages or audio file and returns response from assistant."""
    start_time = time.time()
    try:
        # Excluding prompt, request.messages must be odd length
        # because assistant has not responded yet.
        if (len(request.messages) % 2) == 0:
            raise UsersMessageMissingException

        school_id = user.schoolId if user and user.schoolId else None

        # Pass request to assistant, assuming last message is user's
        assistant_response = await assistant.generate_response(request, user, school_id)
        resp_message = assistant_response.messages[-1]
        assistant_message = resp_message.content
        main_time = time.time()
        # Generate list of quick replies
        # only if no attachments added
        quick_replies = (
            await generate_quick_replies(assistant_message)
            if len(resp_message.attachments) == 0 and main_time - start_time < 2.5
            else []
        )

        end_time = time.time()
        print(
            f"""messages request time elapsed
             full: {end_time - start_time:.2f}s
             base: {main_time - start_time:.2f}s
    quick replies: {end_time - main_time:.2f}s"""
        )
        return MessagesResponse(
            chat=assistant_response.chat,
            messages=assistant_response.messages,
            quickReplies=quick_replies,
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

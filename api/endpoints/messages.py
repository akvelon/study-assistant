from fastapi import APIRouter
from pydantic import BaseModel
from api.assistants.study_assistant import StudyAssistant

assistant = StudyAssistant()
messages_router = APIRouter(prefix='/messages', tags=[""])

class Message(BaseModel):
    id: str
    role: str
    timestamp: int
    content: str
    attachments: list = []

class MessagesRequest(BaseModel):
    messages: list[Message] = []

class MessagesResponse(BaseModel):
    messages: list[Message] = []
    quickReplies: list[str] = []


@messages_router.post('/')
async def messages(request: MessagesRequest) -> MessagesResponse:
    # retrieve message list from request
    messages = request.messages
    if len(messages) > 0:
        # pass messages to study assistant class
        try:
            # recieve response and add to the end of messages
            assistant_response = assistant.generate_response(messages)
            messages.append(assistant_response)
        except Exception as e:
            print(e)
          
    return MessagesResponse(messages=messages, quickReplies=[])

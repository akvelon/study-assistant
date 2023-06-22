from fastapi import APIRouter, Response
from pydantic import BaseModel

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
async def messages(messages: MessagesRequest) -> MessagesResponse:
    data = """
{
    "messages": [
        {
            "id": "001",
            "role": "user",
            "timestamp": 1628912345,
            "content": "Hi, can you help me with my math homework?",
            "attachments": []
        },
        {
            "id": "002",
            "role": "assistant",
            "timestamp": 1628912350,
            "content": "Of course! What do you need help with?",
            "attachments": []
        },
        {
            "id": "003",
            "role": "user",
            "timestamp": 1628912360,
            "content": "I'm stuck on this algebra problem...",
            "attachments": []
        },
        {
            "id": "004",
            "role": "assistant",
            "timestamp": 1628912370,
            "content": "Let's take a look. Can you send me a picture of the problem?",
            "attachments": []
        }
    ],
    "quickReplies": [
        "Sure",
        "No, thanks"
    ]
}"""
    return Response(content=data, media_type="application/json")
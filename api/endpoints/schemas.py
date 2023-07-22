"""API schemas"""
from pydantic import BaseModel


class MessageAttachment(BaseModel):
    """Attachments provide external references for messages"""

    id: str
    title: str
    summary: str
    url: str
    image: str = None


class Message(BaseModel):
    """Messages hold user or assistant replies"""

    id: str
    role: str
    timestamp: int
    content: str
    attachments: list[MessageAttachment] = []


class SearchQuery(BaseModel):
    """Query to search index accepts list of messages"""

    messages: list[Message]


class Chat(BaseModel):
    """Chat holds information regarding ongoing conversation"""

    id: int
    summary: str | None = None


class MessagesRequest(BaseModel):
    """Messages request provides data to complete assistant reply"""

    chat: Chat | None = None
    messages: list[Message] = []


class MessagesResponse(BaseModel):
    """Messages response provides full conversation data with latest assistant reply"""

    chat: Chat | None = None
    messages: list[Message] = []
    quickReplies: list[str] = []


class History(BaseModel):
    """History holds whole conversation history with chat related information"""

    chat: Chat
    user_id: int = None
    messages: list[Message]

    class Config:
        # pylint: disable=missing-class-docstring
        fields = {"user_id": {"exclude": True}}


class HistoryResponse(BaseModel):
    """History response holds all histories available for user"""

    history: list[History] | None = []


class School(BaseModel):
    """Institution related information"""

    id: str
    title: str
    shortName: str


class SchoolsResponse(BaseModel):
    """Schools response holds a list of available institutions"""

    schools: list[School] = []

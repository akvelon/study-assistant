from pydantic import BaseModel


class MessageAttachment(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    image: str = None


class Message(BaseModel):
    id: str
    role: str
    timestamp: int
    content: str
    attachments: list[MessageAttachment] = []


class SearchQuery(BaseModel):
    messages: list[Message]
    attachments: list[MessageAttachment] = []


class Chat(BaseModel):
    id: int
    summary: str | None = None


class MessagesRequest(BaseModel):
    chat: Chat | None = None
    messages: list[Message] = []


class MessagesResponse(BaseModel):
    chat: Chat | None = None
    messages: list[Message] = []
    quickReplies: list[str] = []


class History(BaseModel):
    chat: Chat
    user_id: int
    messages: list[Message]


class HistoryResponse(BaseModel):
    history: list[History] | None = None


class School(BaseModel):
    id: str
    title: str
    shortName: str


class SchoolsResponse(BaseModel):
    schools: list[School] = []

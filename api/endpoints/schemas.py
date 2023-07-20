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
    attachments: list[MessageAttachment] = None

class SearchQuery(BaseModel):
    messages: list[Message]

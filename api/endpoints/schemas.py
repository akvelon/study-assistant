from pydantic import BaseModel

class MessageAttachment(BaseModel):
    id: str
    title: str
    summary: str
    url: str
    image: str

class Message(BaseModel):
    id: str
    role: str
    timestamp: int
    content: str
    attachments: list[MessageAttachment]


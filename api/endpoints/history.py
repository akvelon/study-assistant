from fastapi import APIRouter, Response
from pydantic import BaseModel
from settings import settings

from api.endpoints.messages import Message

history_router = APIRouter(prefix="/history", tags=[""])


class ChatSummary(BaseModel):
    summary: str


class History(BaseModel):
    chat: ChatSummary = ChatSummary(summary="PLACE HOLDER")
    messages: list[Message]


class HistoryResponse(BaseModel):
    history: list[History]


@history_router.get("/")
async def history() -> HistoryResponse:
    history1 = History(
        chat=ChatSummary(summary="Doctor who?"),
        messages=[
            Message(
                id="1",
                role="user",
                timestamp=1622560000,
                content="Knock knock",
                attachments=[],
            ),
            Message(
                id="2",
                role="assistant",
                timestamp=1622560001,
                content="Who's there?",
                attachments=[],
            ),
            Message(
                id="3",
                role="user",
                timestamp=1622560002,
                content="Doctor",
                attachments=[],
            ),
            Message(
                id="4",
                role="assistant",
                timestamp=1622560003,
                content="Doctor who?",
                attachments=[],
            ),
        ],
    )
    history2 = History(
        chat=ChatSummary(summary="The meaning of life, the universe and everything"),
        messages=[
            Message(
                id="1",
                role="user",
                timestamp=1622560000,
                content="What is the meaning of life, the universe and everything?",
                attachments=[],
            ),
            Message(
                id="2",
                role="assistant",
                timestamp=1622560001,
                content="42",
                attachments=[],
            ),
            Message(
                id="3",
                role="user",
                timestamp=1622560002,
                content="How long did it take you to compute that?",
                attachments=[],
            ),
            Message(
                id="4",
                role="assistant",
                timestamp=1622560003,
                content="7.5 million years.",
                attachments=[],
            ),
        ],
    )
    history3 = History(
        chat=ChatSummary(summary="Not financial advice"),
        messages=[
            Message(
                id="1",
                role="user",
                timestamp=1622560000,
                content="Should I buy dogecoin?",
                attachments=[],
            ),
            Message(
                id="2",
                role="assistant",
                timestamp=1622560001,
                content="As in AI language model I can't give you financial advice.",
                attachments=[],
            ),
            Message(
                id="3",
                role="user",
                timestamp=1622560002,
                content="Why am I not surprised?",
                attachments=[],
            ),
            Message(
                id="4",
                role="assistant",
                timestamp=1622560003,
                content="As an AI language model I can't tell you that either.",
                attachments=[],
            ),
            Message(
                id="5",
                role="user",
                timestamp=1622560004,
                content="...",
                attachments=[],
            ),
        ],
    )
    return HistoryResponse(history=[history1, history2, history3])

from fastapi import APIRouter, Response
from pydantic import BaseModel
from settings import settings

history_router = APIRouter(prefix="/history", tags=[""])


@history_router.get("/")
async def history() -> list[dict]:
    return [
        {
            "chat": {"summary": "Doctor who?"},
            "messages": [
                {"role": "user", "content": "Knock knock"},
                {"role": "assistant", "content": "Who's there?"},
                {"role": "user", "content": "Doctor"},
                {"role": "assistant", "content": "Doctor who?"},
            ],
        },
        {
            "chat": {"summary": "The meaning of life, the universe and everything"},
            "messages": [
                {
                    "role": "user",
                    "content": "What is the meaning of life, the universe and everything?",
                },
                {"role": "assistant", "content": "42"},
                {
                    "role": "user",
                    "content": "Wow, that is so deep! How long did it take you to compute that?",
                },
                {"role": "assistant", "content": "7.5 million years."},
            ],
        },
        {
            "chat": {"summary": "Not financial advice"},
            "messages": [
                {
                    "role": "user",
                    "content": "Should I buy dogecoin?",
                },
                {
                    "role": "assistant",
                    "content": "As in AI language model I can't give you financial advice.",
                },
                {
                    "role": "user",
                    "content": "Why am I not surprised?",
                },
                {
                    "role": "assistant",
                    "content": "As an AI language model I can't tell you that either.",
                },
                {
                    "role": "user",
                    "content": "...",
                },
            ],
        },
    ]

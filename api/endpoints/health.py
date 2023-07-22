import os

from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=[""])


@health_router.get("/")
async def health() -> dict:
    return {
        "ok": True,
    }

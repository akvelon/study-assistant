"""Service health check endpoints"""
from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=[""])


@health_router.get("/")
async def health() -> dict:
    """Health check for the API"""
    return {
        "ok": True,
    }

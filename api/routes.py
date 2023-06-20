from fastapi import APIRouter

from api.endpoints.messages import messages_router
from api.endpoints.health import health_router

api_router = APIRouter(prefix='/api')
api_router.include_router(messages_router)
api_router.include_router(health_router)

from fastapi import APIRouter

from api.endpoints.health import health_router
from api.endpoints.messages import messages_router
from api.endpoints.schools import schools_router
from api.endpoints.history import history_router
from api.endpoints.user import user_router
from api.endpoints.search import search_router


api_router = APIRouter(prefix="/v1")
api_router.include_router(health_router)
api_router.include_router(messages_router)
api_router.include_router(schools_router)
api_router.include_router(history_router)
api_router.include_router(user_router)
api_router.include_router(search_router)

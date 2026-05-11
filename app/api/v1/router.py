from app.api.v1 import user_routes, conversation_routes, auth_routes
from fastapi import APIRouter
from app.core.config import settings

api_router = APIRouter(prefix=settings.API_VERSION_PREFIX)

api_router.include_router(user_routes.router)
api_router.include_router(conversation_routes.router)
api_router.include_router(auth_routes.router)
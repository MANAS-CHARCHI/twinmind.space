from fastapi import APIRouter
from app.api.v1.routes.auth import router as auth_router
from app.api.v1.routes.memory_routes import router as memory_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(memory_router)
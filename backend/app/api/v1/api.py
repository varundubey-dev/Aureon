from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.signup import router as signup_router
from app.api.v1.routes.login import router as login_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)

api_router.include_router(signup_router)
api_router.include_router(login_router)

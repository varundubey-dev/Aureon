from fastapi import APIRouter
from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.signup import router as signup_router
from app.api.v1.routes.login import router as login_router
from app.api.v1.routes.password_reset import router as password_reset_router
from app.api.v1.routes.guest import router as guest_router
from app.api.v1.routes.oauth import router as oauth_router
from app.api.v1.routes.rbac_test import router as rbac_test_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health_router)

api_router.include_router(signup_router)
api_router.include_router(login_router)
api_router.include_router(password_reset_router)
api_router.include_router(guest_router)
api_router.include_router(oauth_router)
api_router.include_router(rbac_test_router)
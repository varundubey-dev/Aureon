from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.exceptions.base import AppError

from app.core.exceptions.handlers import (
    app_exception_handler,
    rate_limit_exception_handler
)

from app.services.maintenance.scheduler import (
    start_scheduler,
    stop_scheduler,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()
    

app = FastAPI(title="Aureon API", version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter

app.add_exception_handler(
    AppError,
    app_exception_handler,
)

app.add_exception_handler(
    RateLimitExceeded,
    rate_limit_exception_handler,
)

origins = [
    settings.FRONTEND_URL,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

app.add_middleware(
    SlowAPIMiddleware,
)

app.include_router(api_router)

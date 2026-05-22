from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.api.v1.api import api_router
from app.core.config import settings

from app.services.maintenance.scheduler import (
    start_scheduler,
    stop_scheduler,
)

@asynccontextmanager
async def lifespan(app: FastAPI):

    # Startup
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    

app = FastAPI(title="Aureon API", version="1.0.0", lifespan=lifespan)

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

app.include_router(api_router)

from fastapi import FastAPI
from sqlmodel import SQLModel

from app.api.v1.api import api_router
from app.core.database import engine

# IMPORTANT
from app.models.user import User


app = FastAPI(
    title="Aureon API",
    version="1.0.0"
)


@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)


app.include_router(api_router)
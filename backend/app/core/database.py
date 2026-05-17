from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine, Session
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    DATABASE_URL: str


settings = Settings.model_validate({})

engine = create_engine(
    settings.DATABASE_URL,
    echo=True
)


def get_session():
    with Session(engine) as session:
        yield session
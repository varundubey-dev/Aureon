import pytest

from unittest.mock import patch

from sqlmodel import (
    Session,
    SQLModel,
    create_engine,
)

from sqlalchemy.orm import (
    sessionmaker,
)

from fastapi.testclient import (
    TestClient,
)

from app.main import app
from app.core.config import settings
from app.core.database import get_session
from app.core.rate_limit import limiter

test_engine = create_engine(
    settings.TEST_DATABASE_URL,
)

SQLModel.metadata.create_all(
    test_engine,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture
def session():

    connection = test_engine.connect()
    transaction = connection.begin()

    db = Session(
        bind=connection,
    )

    yield db

    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(session):

    def get_test_session():

        yield session

    app.dependency_overrides[get_session] = get_test_session

    with TestClient(app) as test_client:

        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_rate_limits():

    limiter.reset()


@pytest.fixture(autouse=True)
def mock_send_email():

    with (
        patch(
            "app.api.v1.routes.auth.signup.send_email",
            return_value=True,
        ),
        patch(
            "app.api.v1.routes.auth.password_reset.send_email",
            return_value=True,
        ),
    ):

        yield

@pytest.fixture(autouse=True)
def mock_generate_otp():

    with patch(
        "app.services.auth.otp_service.generate_otp",
        return_value="123456",
    ):
        yield
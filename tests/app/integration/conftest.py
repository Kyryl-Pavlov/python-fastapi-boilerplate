import os
from unittest.mock import patch

# Must be set before any app module is imported so require("SECRET_KEY") doesn't fail
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-bytes!!!!")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-minimum-32-bytes!!")

import bcrypt as _bcrypt  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def fast_bcrypt():
    """Replace bcrypt's 13-round salt with 4-round to keep tests fast."""
    _real_gensalt = _bcrypt.gensalt
    with patch(
        "app.models.user.bcrypt.gensalt",
        side_effect=lambda rounds=12: _real_gensalt(rounds=4),
    ):
        yield


@pytest.fixture(scope="session")
def test_engine(fast_bcrypt):
    import app.models  # noqa: F401  -  ensure all models are registered
    from app.extensions import Base

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def app(test_session_factory):
    from app import create_app
    from app.database import get_db

    fastapi_app = create_app("testing")

    def override_get_db():
        db = test_session_factory()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    return fastapi_app


@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    yield
    from app.extensions import Base
    from sqlalchemy import text

    with test_engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def db_session(test_session_factory):
    """Direct DB session for seeding data or asserting DB state."""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def registered_user(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "Password123!"},
    )
    return {"email": "user@example.com", "password": "Password123!"}


@pytest.fixture
def access_token(client, registered_user):
    res = client.post("/api/v1/auth/login", json=registered_user)
    return res.json()["data"]["access_token"]


@pytest.fixture
def refresh_token(client, registered_user):
    res = client.post("/api/v1/auth/login", json=registered_user)
    return res.json()["data"]["refresh_token"]


@pytest.fixture
def auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def mock_cache(app):
    """Attaches a MagicMock as app.state.cache; restores None after the test."""
    from unittest.mock import MagicMock

    m = MagicMock()
    app.state.cache = m
    yield m
    app.state.cache = None


@pytest.fixture
def gql(client):
    """Post a GraphQL query/mutation; returns the response."""

    def _execute(
        query: str, variables: dict | None = None, headers: dict | None = None
    ):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        return client.post("/graphql", json=payload, headers=headers or {})

    return _execute


@pytest.fixture
def gql_auth_headers(client, registered_user):
    """GraphQL auth via the GraphQL login mutation itself."""
    res = client.post(
        "/graphql",
        json={
            "query": """
                mutation($email: String!, $password: String!) {
                    login(email: $email, password: $password) {
                        data { accessToken refreshToken }
                    }
                }
            """,
            "variables": registered_user,
        },
    )
    tokens = res.json()["data"]["login"]["data"]
    return {
        "access": {"Authorization": f"Bearer {tokens['accessToken']}"},
        "refresh": {"Authorization": f"Bearer {tokens['refreshToken']}"},
    }

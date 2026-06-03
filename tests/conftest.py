import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from api.database import Base, get_db
from api.main import app


@pytest.fixture
def unauth_client(tmp_path):
    """Bare TestClient with isolated SQLite. No auth headers."""
    db_path = tmp_path / "test.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _signup(client: TestClient, email: str, password: str = "supersecret1"):
    response = client.post(
        "/api/auth/signup",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def client(unauth_client):
    """TestClient pre-authenticated as user1@example.com."""
    data = _signup(unauth_client, "user1@example.com")
    unauth_client.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    return unauth_client


@pytest.fixture
def second_client(unauth_client):
    """Helper for owner-isolation tests: signs up a second user against the same DB."""
    data = _signup(unauth_client, "user2@example.com")
    return data

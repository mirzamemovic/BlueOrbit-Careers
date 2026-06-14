from pathlib import Path
from uuid import uuid4

import pytest

from career_portal import create_app
from career_portal.db import db
from career_portal.db import get_db
from career_portal.repositories import CareerRepository


@pytest.fixture()
def app():
    runtime_dir = Path(__file__).resolve().parents[1] / "tests_runtime"
    runtime_dir.mkdir(exist_ok=True)
    database_path = runtime_dir / f"test-{uuid4().hex}.sqlite3"
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": str(database_path),
            "SECRET_KEY": "test-key",
            "JWT_SECRET_KEY": "blueorbit-test-jwt-secret-key-32-chars",
        }
    )
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()
    database_path.unlink(missing_ok=True)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers(client):
    username = f"tester-{uuid4().hex}"
    client.post("/register", json={"username": username, "password": "secret123"})
    response = client.post("/login", json={"username": username, "password": "secret123"})
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def repo(app):
    with app.app_context():
        yield CareerRepository(get_db())

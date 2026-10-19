import os
os.environ["DATABASE_URL"] = "sqlite:///./test_secureops.db"
os.environ["SECRET_KEY"] = "test-only-secret-key-that-is-long-enough-123456789"
from fastapi.testclient import TestClient
import pytest
from app.database import Base, engine, SessionLocal
from app.main import app
from app.models import User
from app.security import hash_password

@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add_all([
        User(username="admin_test", password_hash=hash_password("AdminPassword123!"), role="admin"),
        User(username="analyst_test", password_hash=hash_password("AnalystPassword123!"), role="analyst"),
    ])
    db.commit()
    db.close()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def token(client, username, password):
    r = client.post("/auth/token", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest.fixture
def admin_headers(client):
    return {"Authorization": f"Bearer {token(client, 'admin_test', 'AdminPassword123!')}"}

@pytest.fixture
def analyst_headers(client):
    return {"Authorization": f"Bearer {token(client, 'analyst_test', 'AnalystPassword123!')}"}

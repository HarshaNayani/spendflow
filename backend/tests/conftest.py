import os
import tempfile

# Configure the app BEFORE it is imported: temp SQLite file, no AI key, no seed.
_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["GROQ_API_KEY"] = ""
os.environ["SEED_DEMO"] = "false"
os.environ["SECRET_KEY"] = "test-secret"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402

MANAGER = ("manager@test.dev", "Manager@123")
ADMIN = ("admin@test.dev", "Admin@123")


@pytest.fixture()
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(User(name="Test Manager", email=MANAGER[0], password_hash=hash_password(MANAGER[1]), role="manager"))
    db.add(User(name="Test Admin", email=ADMIN[0], password_hash=hash_password(ADMIN[1]), role="admin"))
    db.commit()
    db.close()
    return TestClient(app)


def login(client, email, password):
    res = client.post("/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def register(client, email="emp@test.dev", name="Test Employee", password="Employee@123"):
    res = client.post("/auth/register", json={"name": name, "email": email, "password": password})
    assert res.status_code == 201, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def submit(client, headers, **overrides):
    body = {
        "amount": 1500,
        "description": "Cab to the client office",
        "expense_date": "2026-10-05",
        "category": "Travel",
    }
    body.update(overrides)
    res = client.post("/expenses", json=body, headers=headers)
    assert res.status_code == 201, res.text
    return res.json()

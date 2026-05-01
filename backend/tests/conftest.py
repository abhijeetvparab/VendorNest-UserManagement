import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import User, UserRole, UserStatus
from auth import hash_password, create_access_token


def auth_header(user: User) -> dict:
    """Return a Bearer auth header for the given user."""
    token = create_access_token({"sub": user.id, "role": user.role.value})
    return {"Authorization": f"Bearer {token}"}

SQLITE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    e = create_engine(
        SQLITE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield e
    e.dispose()


@pytest.fixture(autouse=True)
def tables(engine):
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_user():
    def _make(
        db,
        *,
        email,
        password="TestPass1!",
        role=UserRole.CUSTOMER,
        status=UserStatus.ACTIVE,
        first_name="Test",
        last_name="User",
    ):
        user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone_number="9876543210",
            address="123 Main Street City",
            password_hash=hash_password(password),
            role=role,
            status=status,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _make

"""Test fixtures.

Every test gets a fresh in-memory SQLite database, so tests never touch the real
PostgreSQL instance and never depend on each other's data.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite://")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.db import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def make_ticket(client):
    def _make(**overrides):
        payload = {
            "subject": "Cannot log in to the portal",
            "description": "Password reset email never arrives.",
            "category": "ACCOUNT",
            "priority": "HIGH",
            "requester_name": "Asha Verma",
            "requester_email": "asha@example.com",
        }
        payload.update(overrides)
        response = client.post("/api/tickets", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make

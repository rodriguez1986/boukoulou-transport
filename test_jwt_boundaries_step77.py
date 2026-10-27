"""Étape 77 : limites de validité et ordre chronologique des JWT."""
from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import security
from app.db import get_db

KEY = "step77-only-testing-jwt-signing-key-of-sufficient-length"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    app = FastAPI()

    @app.get("/protected")
    def protected(u=Depends(security.user)):
        return {"id": u.id}

    class DB:
        def get(self, model, uid):
            return SimpleNamespace(id=17, is_active=True, token_version=3) if uid == 17 else None

    app.dependency_overrides[get_db] = lambda: DB()
    return TestClient(app)


def status(client, data):
    signed = jwt.encode(data, KEY, algorithm="HS256")
    return client.get("/protected", headers={"Authorization": "Bearer " + signed}).status_code


def claims():
    now = int(datetime.now(timezone.utc).timestamp())
    return {"sub": "17", "tv": 3, "iat": now, "nbf": now, "exp": now + 600}


def test_exactly_maximum_signed_lifetime_is_accepted(client):
    assert status(client, claims()) == 200


def test_one_second_over_maximum_signed_lifetime_is_rejected(client):
    data = claims()
    data["exp"] += 1
    assert status(client, data) == 401


def test_equal_issued_and_not_before_is_accepted(client):
    assert status(client, claims()) == 200


def test_issued_after_not_before_is_rejected(client):
    data = claims()
    data["iat"] += 1
    assert status(client, data) == 401


def test_expiration_equal_not_before_is_rejected(client):
    data = claims()
    data["nbf"] = data["exp"]
    assert status(client, data) == 401


def test_expiration_before_not_before_is_rejected(client):
    data = claims()
    data["nbf"] = data["exp"] + 1
    assert status(client, data) == 401


def test_expiration_equal_issued_is_rejected(client):
    data = claims()
    data["iat"] = data["exp"]
    data["nbf"] = data["exp"]
    assert status(client, data) == 401


def test_legacy_token_without_pair_still_accepted(client):
    data = claims()
    del data["iat"]
    del data["nbf"]
    assert status(client, data) == 200

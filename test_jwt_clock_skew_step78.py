"""Étape 78 : tolérance d'horloge bornée, expiration jamais prolongée."""
from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import security
from app.db import get_db

KEY = "step78-only-testing-jwt-signing-key-of-sufficient-length"


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


@pytest.mark.parametrize("offset", [1, 3, 5])
def test_small_future_clock_skew_accepted(client, offset):
    data = claims()
    data["iat"] += offset
    data["nbf"] += offset
    data["exp"] += offset
    assert status(client, data) == 200


@pytest.mark.parametrize("offset", [6, 30, 3600])
def test_large_future_clock_skew_rejected(client, offset):
    data = claims()
    data["iat"] += offset
    data["nbf"] += offset
    data["exp"] += offset
    assert status(client, data) == 401


def test_expired_token_not_rescued_by_skew(client):
    data = claims()
    data["exp"] = int(datetime.now(timezone.utc).timestamp()) - 1
    assert status(client, data) == 401


def test_expiration_at_current_second_not_rescued(client):
    data = claims()
    data["exp"] = int(datetime.now(timezone.utc).timestamp())
    assert status(client, data) == 401


def test_legacy_expiration_still_strict(client):
    data = claims()
    del data["iat"]
    del data["nbf"]
    data["exp"] = int(datetime.now(timezone.utc).timestamp()) - 1
    assert status(client, data) == 401


def test_future_nbf_only_still_rejected(client):
    data = claims()
    del data["iat"]
    data["nbf"] += 2
    assert status(client, data) == 401

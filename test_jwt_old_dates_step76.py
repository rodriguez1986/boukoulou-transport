"""Étape 76 : rejet des dates JWT trop anciennes, compatibilité historique."""
from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import security
from app.db import get_db

KEY = "step76-only-testing-jwt-signing-key-of-sufficient-length"


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


def request(client, data):
    signed = jwt.encode(data, KEY, algorithm="HS256")
    return client.get("/protected", headers={"Authorization": "Bearer " + signed}).status_code


def base():
    now = int(datetime.now(timezone.utc).timestamp())
    return {"sub": "17", "tv": 3, "iat": now - 5, "nbf": now - 5, "exp": now + 595}


def test_current_dates_accepted(client):
    assert request(client, base()) == 200


@pytest.mark.parametrize("field", ["iat", "nbf"])
def test_ancient_date_rejected(client, field):
    data = base()
    data[field] -= 3600
    assert request(client, data) == 401


def test_ancient_both_dates_rejected(client):
    data = base()
    data["iat"] -= 3600
    data["nbf"] -= 3600
    assert request(client, data) == 401


def test_old_pair_even_with_future_expiration_rejected(client):
    data = base()
    data["iat"] -= 3600
    data["nbf"] -= 3600
    data["exp"] += 3600
    assert request(client, data) == 401


def test_historical_token_without_temporal_pair_accepted(client):
    data = base()
    data.pop("iat")
    data.pop("nbf")
    assert request(client, data) == 200


def test_single_temporal_claim_still_rejected(client):
    data = base()
    data.pop("nbf")
    assert request(client, data) == 401


def test_new_token_accepted(client):
    signed = security.token(SimpleNamespace(id=17, token_version=3))
    return_status = client.get("/protected", headers={"Authorization": "Bearer " + signed}).status_code
    assert return_status == 200

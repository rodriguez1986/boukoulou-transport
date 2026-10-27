"""Vérification de la durée de vie réelle d'un JWT signé."""
from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import security
from app.db import get_db

KEY = 'step74-test-only-signing-key-with-adequate-length'


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(security, 'SECRET', KEY)
    monkeypatch.setattr(security, 'MIN', 10)
    app = FastAPI()

    @app.get('/protected')
    def protected(u=Depends(security.user)):
        return {'id': u.id}

    class DB:
        def get(self, model, uid):
            if uid == 17:
                return SimpleNamespace(id=17, is_active=True, token_version=3)
            return None

    app.dependency_overrides[get_db] = lambda: DB()
    return TestClient(app)


def payload():
    now = int(datetime.now(timezone.utc).timestamp())
    return {'sub': '17', 'tv': 3, 'iat': now - 5, 'nbf': now - 5, 'exp': now + 595}


def status(client, data):
    signed = jwt.encode(data, KEY, algorithm='HS256')
    return client.get('/protected', headers={'Authorization': 'Bearer ' + signed}).status_code


def test_exact_max_lifetime_allowed(client):
    assert status(client, payload()) == 200


def test_excessive_lifetime_rejected(client):
    data = payload()
    data['exp'] += 1
    assert status(client, data) == 401


def test_excessive_lifetime_even_with_near_expiry(client):
    data = payload()
    data['iat'] -= 1000
    data['nbf'] -= 1000
    data['exp'] = int(datetime.now(timezone.utc).timestamp()) + 20
    assert status(client, data) == 401


def test_nbf_cannot_hide_excessive_lifetime(client):
    data = payload()
    data['iat'] -= 1000
    assert status(client, data) == 401


def test_legacy_token_remains_accepted(client):
    data = payload()
    del data['iat']
    del data['nbf']
    assert status(client, data) == 200


def test_issued_token_respects_configured_lifetime(client):
    encoded = security.token(SimpleNamespace(id=17, token_version=3))
    decoded = jwt.decode(encoded, KEY, algorithms=['HS256'])
    assert decoded['exp'] - decoded['iat'] == 600
    assert decoded['exp'] - decoded['nbf'] == 600

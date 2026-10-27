"""Étape 75 : présence atomique des champs temporels JWT."""
from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import security
from app.db import get_db

KEY = 'step75-test-only-signing-key-with-adequate-length'


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
            return SimpleNamespace(id=17, is_active=True, token_version=3) if uid == 17 else None

    app.dependency_overrides[get_db] = lambda: DB()
    return TestClient(app)


def claims():
    now = int(datetime.now(timezone.utc).timestamp())
    return {'sub': '17', 'tv': 3, 'iat': now - 5, 'nbf': now - 5, 'exp': now + 595}


def status(client, data):
    encoded = jwt.encode(data, KEY, algorithm='HS256')
    return client.get('/protected', headers={'Authorization': 'Bearer ' + encoded}).status_code


@pytest.mark.parametrize('missing', ['iat', 'nbf'])
def test_single_temporal_claim_rejected(client, missing):
    data = claims()
    del data[missing]
    assert status(client, data) == 401


@pytest.mark.parametrize('missing', ['iat', 'nbf'])
def test_single_temporal_claim_cannot_bypass_lifetime(client, missing):
    data = claims()
    data['exp'] += 1000
    del data[missing]
    assert status(client, data) == 401


def test_complete_temporal_pair_allowed(client):
    assert status(client, claims()) == 200


def test_historical_token_without_both_still_allowed(client):
    data = claims()
    del data['iat']
    del data['nbf']
    assert status(client, data) == 200


def test_new_token_contains_both_claims(client):
    signed = security.token(SimpleNamespace(id=17, token_version=3))
    decoded = jwt.decode(signed, KEY, algorithms=['HS256'])
    assert decoded['iat'] == decoded['nbf']
    assert decoded['exp'] - decoded['iat'] == 600

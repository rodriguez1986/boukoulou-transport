"""Contrôles des dates JWT, sans base de données externe."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from app import security
from app.db import get_db

KEY = 'step73-local-test-only-signing-key-with-adequate-length'

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(security, 'SECRET', KEY)
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
    return {'sub': '17', 'tv': 3, 'exp': now + 600, 'iat': now - 10, 'nbf': now - 10}

def response(client, payload):
    return client.get('/protected', headers={'Authorization': 'Bearer ' + jwt.encode(payload, KEY, algorithm='HS256')})

def test_valid_temporal_claims(client):
    assert response(client, claims()).status_code == 200

def test_legacy_without_temporal_claims(client):
    payload = claims(); del payload['iat']; del payload['nbf']
    assert response(client, payload).status_code == 200

@pytest.mark.parametrize('field', ['iat', 'nbf'])
@pytest.mark.parametrize('value', [True, False, '1234567890', 1.5, 0, -1, None])
def test_bad_timestamp_type(client, field, value):
    payload = claims(); payload[field] = value
    assert response(client, payload).status_code == 401

@pytest.mark.parametrize('field', ['iat', 'nbf'])
def test_future_date_rejected(client, field):
    payload = claims(); payload[field] = payload['exp'] + 100
    assert response(client, payload).status_code == 401

def test_iat_after_nbf_rejected(client):
    payload = claims(); payload['iat'] = payload['nbf'] + 1
    assert response(client, payload).status_code == 401

def test_token_emits_iat_and_nbf(monkeypatch):
    monkeypatch.setattr(security, 'SECRET', KEY)
    value = security.token(SimpleNamespace(id=17, token_version=3))
    decoded = jwt.decode(value, KEY, algorithms=['HS256'])
    assert type(decoded['iat']) is int
    assert type(decoded['nbf']) is int
    assert decoded['iat'] == decoded['nbf']
    assert decoded['exp'] > decoded['iat']

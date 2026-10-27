"""Tests HTTP des champs JWT obligatoires (aucune base réelle)."""
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
import jwt
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app import security
from app.db import get_db

SECRET = 'step72-test-only-jwt-signing-key-32-bytes-minimum'

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(security, 'SECRET', SECRET)
    app = FastAPI()
    @app.get('/protected')
    def protected(u=__import__('fastapi').Depends(security.user)):
        return {'id': u.id}
    class DB:
        def get(self, model, uid):
            return SimpleNamespace(id=17, is_active=True, token_version=3) if uid == 17 else None
    app.dependency_overrides[get_db] = lambda: DB()
    return TestClient(app)

def request(client, claims):
    encoded = jwt.encode(claims, SECRET, algorithm='HS256')
    return client.get('/protected', headers={'Authorization': 'Bearer ' + encoded})

def valid():
    return {'sub':'17', 'tv':3, 'exp':int((datetime.now(timezone.utc)+timedelta(minutes=10)).timestamp())}

def test_valid_claims(client):
    assert request(client, valid()).status_code == 200

@pytest.mark.parametrize('missing', ['sub','tv','exp'])
def test_missing_claim(client, missing):
    claims = valid(); del claims[missing]
    assert request(client, claims).status_code == 401

@pytest.mark.parametrize('subject', [17, True, '0', '-17', ' 17', '17 ', '1.7', '١٧', 'abc', ''])
def test_invalid_subject(client, subject):
    claims = valid(); claims['sub'] = subject
    assert request(client, claims).status_code == 401

@pytest.mark.parametrize('expiry', [True, 'not-a-date', '9999999999', 0, -1, 1.5])
def test_invalid_expiry(client, expiry):
    claims = valid(); claims['exp'] = expiry
    assert request(client, claims).status_code == 401

@pytest.mark.parametrize('version', [True, '3', -1, 3.0, None])
def test_invalid_version(client, version):
    claims = valid(); claims['tv'] = version
    assert request(client, claims).status_code == 401

def test_expired(client):
    claims = valid(); claims['exp'] = int((datetime.now(timezone.utc)-timedelta(minutes=1)).timestamp())
    assert request(client, claims).status_code == 401

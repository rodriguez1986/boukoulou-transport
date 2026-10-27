"""Étape 81 : erreurs d'authentification HTTP uniformes, sans fuite."""
from types import SimpleNamespace
import jwt
import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from app import security
from app.db import get_db

KEY = 'step81-test-key-only-very-long-and-unique-xyz'

class DB:
    def get(self, model, uid):
        return SimpleNamespace(id=uid, is_active=True, token_version=2, role=SimpleNamespace(value='ADMIN'))

@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(security, 'SECRET', KEY)
    api = FastAPI()
    api.dependency_overrides[get_db] = lambda: DB()
    @api.get('/protected')
    def protected(u=Depends(security.user)):
        return {'id': u.id}
    @api.get('/optional')
    def optional(u=Depends(security.utilisateur_optionnel)):
        return {'id': u.id if u else None}
    return TestClient(api)

@pytest.mark.parametrize('header', [None, 'Basic abc', 'Bearer', 'Bearer ', 'Bearer not.a.jwt', 'Token abc'])
def test_protected_invalid_bearer_returns_uniform_401(client, header):
    response = client.get('/protected', headers={'Authorization': header} if header is not None else {})
    assert response.status_code == 401
    assert response.json() == {'detail': 'Token invalide'}
    assert response.headers['www-authenticate'] == 'Bearer'
    assert 'not.a.jwt' not in response.text

@pytest.mark.parametrize('header', ['Basic abc', 'Bearer', 'Bearer invalid'])
def test_optional_invalid_header_is_401(client, header):
    response = client.get('/optional', headers={'Authorization': header})
    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


def test_optional_without_header_remains_anonymous(client):
    assert client.get('/optional').json() == {'id': None}


def test_valid_token_still_works(client):
    from datetime import datetime, timezone
    now = int(datetime.now(timezone.utc).timestamp())
    payload = {'sub': '17', 'tv': 2, 'iat': now, 'nbf': now, 'exp': now + 300}
    response = client.get('/protected', headers={'Authorization': 'Bearer ' + jwt.encode(payload, KEY, algorithm='HS256')})
    assert response.status_code == 200
    assert response.json() == {'id': 17}

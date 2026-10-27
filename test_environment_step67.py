"""Étape 67 : protection des environnements contre le seed involontaire."""
import pytest
from fastapi.testclient import TestClient
from app import main

@pytest.mark.parametrize('environment', ['production', 'test', 'staging', '', 'PRODUCTION'])
def test_seed_interdit_hors_development(monkeypatch, environment):
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '1')
    if environment:
        monkeypatch.setenv('BOUKOULOU_ENV', environment)
    else:
        monkeypatch.delenv('BOUKOULOU_ENV', raising=False)
    monkeypatch.setattr(main, 'SessionLocal', lambda: pytest.fail('connexion DB interdite'))
    with pytest.raises(RuntimeError, match='BOUKOULOU_ENV=development|JWT_ENV_INVALID'):
        with TestClient(main.app):
            pass

@pytest.mark.parametrize('environment', ['production', 'test', 'staging', ''])
def test_seed_desactive_ne_touche_pas_base(monkeypatch, environment):
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '0')
    monkeypatch.setenv('JWT_SECRET', 'step68-test-only-secret-at-least-32-bytes')
    monkeypatch.setattr('app.security.SECRET', 'step68-test-only-secret-at-least-32-bytes')
    monkeypatch.setenv('BOUKOULOU_ENV', environment)
    monkeypatch.setattr(main, 'SessionLocal', lambda: pytest.fail('connexion DB interdite'))
    with TestClient(main.app) as client:
        assert client.get('/health').json() == {'status': 'ok'}

def test_seed_development_explicite_autorise(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '1')
    monkeypatch.setenv('BOUKOULOU_ENV', 'development')
    calls=[]
    class Query:
        def filter_by(self, **kwargs): return self
        def first(self): return object()
    class Session:
        def query(self, model): return Query()
        def commit(self): calls.append('commit')
        def close(self): calls.append('close')
    monkeypatch.setattr(main, 'SessionLocal', Session)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200
    assert calls == ['commit', 'close']

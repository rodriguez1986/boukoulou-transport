"""Étape 66 : échecs d'initialisation et nettoyage des ressources."""
import pytest
from fastapi.testclient import TestClient
from app import main


def test_erreur_startup_propagee_et_aucune_requete_servie(monkeypatch):
    appels = []
    def seed_en_echec():
        appels.append('seed')
        raise RuntimeError('initialisation impossible')
    monkeypatch.setattr(main, 'seed', seed_en_echec)
    with pytest.raises(RuntimeError, match='initialisation impossible'):
        with TestClient(main.app) as client:
            client.get('/health')
    assert appels == ['seed']


def test_seed_erreur_commit_rollback_et_close(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV', 'development')
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '1')
    events = []
    class FakeQuery:
        def filter_by(self, **kwargs): return self
        def first(self): return object()
    class FakeSession:
        def query(self, model): return FakeQuery()
        def commit(self):
            events.append('commit')
            raise ValueError('transaction refusée')
        def rollback(self): events.append('rollback')
        def close(self): events.append('close')
    monkeypatch.setattr(main, 'SessionLocal', FakeSession)
    with pytest.raises(ValueError, match='transaction refusée'):
        with TestClient(main.app):
            pass
    assert events == ['commit', 'rollback', 'close']


def test_seed_erreur_lecture_rollback_et_close(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV', 'development')
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '1')
    events = []
    class FakeSession:
        def query(self, model): raise RuntimeError('lecture refusée')
        def rollback(self): events.append('rollback')
        def close(self): events.append('close')
    monkeypatch.setattr(main, 'SessionLocal', FakeSession)
    with pytest.raises(RuntimeError, match='lecture refusée'):
        with TestClient(main.app):
            pass
    assert events == ['rollback', 'close']


def test_cycles_successifs_sans_seed_ni_session(monkeypatch):
    monkeypatch.delenv('BOUKOULOU_ENABLE_DEV_SEED', raising=False)
    def connexion_interdite():
        raise AssertionError('connexion inattendue')
    monkeypatch.setattr(main, 'SessionLocal', connexion_interdite)
    for _ in range(3):
        with TestClient(main.app) as client:
            assert client.get('/health').json() == {'status': 'ok'}

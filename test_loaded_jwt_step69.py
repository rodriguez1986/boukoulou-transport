"""Vérification JWT à l'exécution : aucun secret réel utilisé."""
import pytest
from fastapi.testclient import TestClient
from app import main
from app.startup_config_step68 import validate_loaded_jwt_secret

STRONG = 'jwt-test-secret-that-is-longer-than-32-bytes-only'
OTHER = 'a-different-jwt-test-secret-more-than-32-bytes'

def test_secret_identique_accepte():
    assert validate_loaded_jwt_secret({'APP_ENV':'production','JWT_SECRET':STRONG}, STRONG)

def test_secret_charge_different_refuse():
    with pytest.raises(RuntimeError, match='incohérente'):
        validate_loaded_jwt_secret({'APP_ENV':'production','JWT_SECRET':STRONG}, OTHER)

def test_secret_de_developpement_refuse_en_production():
    with pytest.raises(RuntimeError, match='incohérente'):
        validate_loaded_jwt_secret({'APP_ENV':'production','JWT_SECRET':STRONG},
                                   'boukoulou-dev-only-insecure-key-not-for-production-2026')

def test_secret_invalide_refuse_avant_comparaison():
    with pytest.raises(RuntimeError, match='JWT_SECRET'):
        validate_loaded_jwt_secret({'APP_ENV':'production','JWT_SECRET':'short'}, 'short')

def test_demarrage_refuse_cle_chargee_differente_avant_seed(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV','production')
    monkeypatch.delenv('APP_ENV',raising=False)
    monkeypatch.setenv('JWT_SECRET',STRONG)
    monkeypatch.delenv('BOUKOULOU_ENABLE_DEV_SEED',raising=False)
    monkeypatch.setattr('app.security.SECRET', OTHER)
    monkeypatch.setattr(main,'seed',lambda: pytest.fail('seed interdit'))
    with pytest.raises(RuntimeError, match='JWT_RUNTIME_INVALID'):
        with TestClient(main.app): pass

def test_demarrage_accepte_cle_coherente(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV','production')
    monkeypatch.delenv('APP_ENV',raising=False)
    monkeypatch.setenv('JWT_SECRET',STRONG)
    monkeypatch.delenv('BOUKOULOU_ENABLE_DEV_SEED',raising=False)
    monkeypatch.setattr('app.security.SECRET', STRONG)
    monkeypatch.setattr(main,'SessionLocal',lambda: pytest.fail('aucune session attendue'))
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200

"""Étape 68 : vérification des paramètres au démarrage sans base réelle."""
import pytest
from fastapi.testclient import TestClient
from app import main
from app.startup_config_step68 import validate_startup_config

STRONG = 'integration-test-secret-unique-and-at-least-32-bytes'

@pytest.mark.parametrize('secret', [None, '', 'short', 'dev-secret', 'boukoulou-dev-only-insecure-key-not-for-production-2026'])
def test_production_refuse_secret_invalide(secret):
    env={'BOUKOULOU_ENV':'production'}
    if secret is not None: env['JWT_SECRET']=secret
    with pytest.raises(RuntimeError, match='JWT_SECRET'):
        validate_startup_config(env)

def test_production_accepte_secret_robuste():
    assert validate_startup_config({'BOUKOULOU_ENV':'production','JWT_SECRET':STRONG}) == 'production'

def test_alias_prod_accepte_secret_robuste():
    assert validate_startup_config({'APP_ENV':'prod','JWT_SECRET':STRONG}) == 'production'

@pytest.mark.parametrize('name', ['BOUKOULOU_ENV','APP_ENV'])
def test_environnement_inconnu_refuse(name):
    with pytest.raises(RuntimeError, match='inconnu'):
        validate_startup_config({name:'invalid-environment'})

def test_environnements_contradictoires_refuses():
    with pytest.raises(RuntimeError, match='contradictoires'):
        validate_startup_config({'BOUKOULOU_ENV':'development','APP_ENV':'production'})

def test_seed_production_refuse_meme_avec_secret_valide():
    with pytest.raises(RuntimeError, match='Seed interdit'):
        validate_startup_config({'BOUKOULOU_ENV':'production','JWT_SECRET':STRONG,'BOUKOULOU_ENABLE_DEV_SEED':'1'})

def test_demarrage_production_invalide_avant_session(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV','production')
    monkeypatch.delenv('APP_ENV',raising=False)
    monkeypatch.delenv('JWT_SECRET',raising=False)
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED','0')
    monkeypatch.setattr(main,'SessionLocal',lambda: pytest.fail('session DB interdite'))
    with pytest.raises(RuntimeError, match='JWT_ENV_INVALID'):
        with TestClient(main.app): pass

def test_demarrage_production_valide_sans_seed(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV','production')
    monkeypatch.delenv('APP_ENV',raising=False)
    monkeypatch.setenv('JWT_SECRET',STRONG)
    monkeypatch.setattr('app.security.SECRET', STRONG)
    monkeypatch.delenv('BOUKOULOU_ENABLE_DEV_SEED',raising=False)
    monkeypatch.setattr(main,'SessionLocal',lambda: pytest.fail('session DB interdite'))
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200

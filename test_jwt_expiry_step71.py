"""Contrats de durée JWT et cohérence des valeurs chargées."""
import pytest
from app.jwt_expiry_step71 import get_access_token_minutes, validate_loaded_access_token_minutes


@pytest.mark.parametrize('value', ['0', '-1', 'abc', '1.5', '', ' 10', '10 ', '١٢', '1e3'])
def test_invalid_minutes(value):
    with pytest.raises(RuntimeError, match='ACCESS_TOKEN_MINUTES'):
        get_access_token_minutes({'ACCESS_TOKEN_MINUTES': value})


def test_default():
    assert get_access_token_minutes({}) == 480


def test_development_can_use_longer_duration():
    assert get_access_token_minutes({'APP_ENV': 'development', 'ACCESS_TOKEN_MINUTES': '2880'}) == 2880


@pytest.mark.parametrize('mode_key,mode', [('APP_ENV', 'production'), ('APP_ENV', 'prod'), ('BOUKOULOU_ENV', 'production')])
def test_production_limit(mode_key, mode):
    assert get_access_token_minutes({mode_key: mode, 'ACCESS_TOKEN_MINUTES': '1440'}) == 1440
    with pytest.raises(RuntimeError, match='limite de production'):
        get_access_token_minutes({mode_key: mode, 'ACCESS_TOKEN_MINUTES': '1441'})


def test_loaded_minutes_match():
    assert validate_loaded_access_token_minutes({'ACCESS_TOKEN_MINUTES': '30'}, 30)


def test_loaded_minutes_mismatch():
    with pytest.raises(RuntimeError, match='redémarrage requis'):
        validate_loaded_access_token_minutes({'ACCESS_TOKEN_MINUTES': '30'}, 480)


def test_loaded_minutes_rejects_boolean():
    with pytest.raises(RuntimeError, match='redémarrage requis'):
        validate_loaded_access_token_minutes({'ACCESS_TOKEN_MINUTES': '1'}, True)


def test_startup_checks_expiry_before_seed(monkeypatch):
    from fastapi.testclient import TestClient
    from app import main
    monkeypatch.setattr(main, 'validate_startup_config', lambda: None)
    monkeypatch.setattr(main, 'validate_loaded_jwt_secret', lambda: True)
    monkeypatch.setattr(main, 'validate_loaded_jwt_runtime_config', lambda: (_ for _ in ()).throw(RuntimeError('invalid expiry')))
    monkeypatch.setattr(main, 'seed', lambda: pytest.fail('seed must not run'))
    with pytest.raises(RuntimeError, match='JWT_RUNTIME_INVALID'):
        with TestClient(main.app):
            pass

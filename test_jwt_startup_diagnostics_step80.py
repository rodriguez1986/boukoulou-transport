"""Étape 80 : arrêt fail-closed et diagnostic JWT sans fuite."""
import logging
import pytest
from app.jwt_startup_diagnostics_step80 import validate_jwt_startup_safely


def test_valid_configuration_runs_both_checks():
    calls = []
    assert validate_jwt_startup_safely(lambda: calls.append('env'), lambda: calls.append('runtime'))
    assert calls == ['env', 'runtime']


@pytest.mark.parametrize('error', [RuntimeError, ValueError, KeyError, TypeError])
def test_environment_error_is_redacted_and_prevents_runtime_check(caplog, error):
    calls = []
    secret = 'SUPER_SECRET_DO_NOT_LOG_123'
    def fail():
        raise error(secret)
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match='JWT_ENV_INVALID') as caught:
        validate_jwt_startup_safely(fail, lambda: calls.append('runtime'))
    assert calls == []
    assert secret not in str(caught.value)
    assert secret not in caplog.text
    assert caught.value.__cause__ is None
    assert 'JWT_ENV_INVALID' in caplog.text


@pytest.mark.parametrize('error', [RuntimeError, ValueError, KeyError, TypeError])
def test_runtime_error_is_redacted(caplog, error):
    secret = 'SUPER_SECRET_DO_NOT_LOG_456'
    def fail():
        raise error(secret)
    with caplog.at_level(logging.ERROR), pytest.raises(RuntimeError, match='JWT_RUNTIME_INVALID') as caught:
        validate_jwt_startup_safely(lambda: None, fail)
    assert secret not in str(caught.value)
    assert secret not in caplog.text
    assert caught.value.__cause__ is None
    assert 'JWT_RUNTIME_INVALID' in caplog.text


def test_lifespan_validation_failure_prevents_seed(monkeypatch):
    from app import main
    from fastapi.testclient import TestClient
    calls = []
    monkeypatch.setattr(main, 'validate_startup_config', lambda: (_ for _ in ()).throw(RuntimeError('SENSITIVE_VALUE')))
    monkeypatch.setattr(main, 'validate_loaded_jwt_runtime_config', lambda: calls.append('runtime'))
    monkeypatch.setattr(main, 'seed', lambda: calls.append('seed'))
    with pytest.raises(RuntimeError, match='JWT_ENV_INVALID') as caught:
        with TestClient(main.app):
            pass
    assert 'SENSITIVE_VALUE' not in str(caught.value)
    assert calls == []


def test_lifespan_runtime_failure_prevents_seed(monkeypatch):
    from app import main
    from fastapi.testclient import TestClient
    calls = []
    monkeypatch.setattr(main, 'validate_startup_config', lambda: calls.append('env'))
    monkeypatch.setattr(main, 'validate_loaded_jwt_runtime_config', lambda: (_ for _ in ()).throw(ValueError('SENSITIVE_VALUE')))
    monkeypatch.setattr(main, 'seed', lambda: calls.append('seed'))
    with pytest.raises(RuntimeError, match='JWT_RUNTIME_INVALID') as caught:
        with TestClient(main.app):
            pass
    assert 'SENSITIVE_VALUE' not in str(caught.value)
    assert calls == ['env']

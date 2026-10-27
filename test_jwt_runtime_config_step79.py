"""Étape 79 : cohérence de configuration de l'émetteur et du vérificateur."""
from types import SimpleNamespace
import jwt
import pytest
from app import security
from app.jwt_runtime_config_step79 import validate_loaded_jwt_runtime_config

KEY = "step79-test-only-strong-secret-for-configuration-checks"
ENV = {"APP_ENV": "test", "JWT_SECRET": KEY, "ACCESS_TOKEN_MINUTES": "10"}


def test_valid_configuration(monkeypatch):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    assert validate_loaded_jwt_runtime_config(ENV) is True


@pytest.mark.parametrize("bad", ["HS384", "HS512", "none", "hs256", "", 256, None])
def test_reject_wrong_algorithm(monkeypatch, bad):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    if bad is None:
        monkeypatch.setattr(security, "JWT_ALGORITHM", None)
        with pytest.raises(RuntimeError, match="Algorithme"):
            validate_loaded_jwt_runtime_config(ENV)
    else:
        with pytest.raises(RuntimeError, match="Algorithme"):
            validate_loaded_jwt_runtime_config(ENV, algorithm=bad)


@pytest.mark.parametrize("bad", [0, 1, 6, -1, True, "5", 5.0])
def test_reject_wrong_skew(monkeypatch, bad):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    with pytest.raises(RuntimeError, match="Tolérance"):
        validate_loaded_jwt_runtime_config(ENV, clock_skew_seconds=bad)


def test_reject_secret_mismatch(monkeypatch):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    with pytest.raises(RuntimeError, match="Clé JWT"):
        validate_loaded_jwt_runtime_config(ENV, secret="different-secret")


def test_reject_expiry_mismatch(monkeypatch):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    with pytest.raises(RuntimeError, match="Durée JWT"):
        validate_loaded_jwt_runtime_config(ENV, minutes=11)


def test_issuer_uses_configured_algorithm(monkeypatch):
    monkeypatch.setattr(security, "SECRET", KEY)
    monkeypatch.setattr(security, "MIN", 10)
    encoded = security.token(SimpleNamespace(id=12, token_version=2))
    assert jwt.get_unverified_header(encoded)["alg"] == security.JWT_ALGORITHM == "HS256"
    decoded = jwt.decode(encoded, KEY, algorithms=[security.JWT_ALGORITHM])
    assert decoded["sub"] == "12"

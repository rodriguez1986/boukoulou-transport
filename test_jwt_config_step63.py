"""Contrats de configuration sans démarrage du serveur ni secrets réels."""
import pytest
from app.jwt_config_step63 import DEV_ONLY_SECRET, get_jwt_secret


def test_dev_without_key_uses_explicit_dev_only_value():
    assert get_jwt_secret({}) == DEV_ONLY_SECRET
    assert len(DEV_ONLY_SECRET.encode()) >= 32

@pytest.mark.parametrize("mode", ["production", "prod", "PRODUCTION"])
@pytest.mark.parametrize("secret", [None, "", "dev-secret", "CHANGE_THIS_SECRET", "CHANGE_THIS_IN_PRODUCTION", "short", DEV_ONLY_SECRET, "x" * 31, " " + "x" * 32])
def test_production_refuses_unsafe_secret(mode, secret):
    env = {"APP_ENV": mode}
    if secret is not None:
        env["JWT_SECRET"] = secret
    with pytest.raises(RuntimeError, match="JWT_SECRET"):
        get_jwt_secret(env)

@pytest.mark.parametrize("mode", ["production", "prod", "development"])
def test_configured_strong_secret_is_preserved(mode):
    value = "test-only-configured-long-jwt-secret-not-a-real-key-123456"
    assert get_jwt_secret({"APP_ENV": mode, "JWT_SECRET": value}) == value

def test_dev_warns_on_weak_configured_secret():
    with pytest.warns(RuntimeWarning, match="JWT_SECRET"):
        assert get_jwt_secret({"JWT_SECRET": "dev-secret"}) == "dev-secret"

def test_compose_requires_explicit_secret():
    from pathlib import Path
    compose = (Path(__file__).parent / "docker-compose.yml").read_text()
    assert "JWT_SECRET: ${JWT_SECRET:?" in compose
    assert "JWT_SECRET: CHANGE_THIS_IN_PRODUCTION" not in compose

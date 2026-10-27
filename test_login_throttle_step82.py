"""Étape 82 : verrouillage temporaire et réponses de connexion."""
from types import SimpleNamespace
from fastapi import HTTPException
import pytest
from app import main
from app import login_throttle_step82 as throttle

@pytest.fixture(autouse=True)
def reset_throttle():
    with throttle._lock:
        throttle._attempts.clear()
    yield
    with throttle._lock:
        throttle._attempts.clear()


def test_five_failures_block_for_fifteen_minutes():
    for i in range(4):
        assert not throttle.record_failure('Agent1', now=100 + i)
    assert throttle.record_failure(' Agent1 ', now=104)
    assert throttle.is_blocked('agent1', now=105)
    assert not throttle.is_blocked('agent1', now=1004)


def test_window_resets_without_lockout():
    for i in range(4):
        throttle.record_failure('agent', now=i)
    assert not throttle.record_failure('agent', now=901)
    assert not throttle.is_blocked('agent', now=902)


def test_success_clears_attempts():
    for i in range(4):
        throttle.record_failure('agent', now=i)
    throttle.clear_failures('agent')
    assert not throttle.record_failure('agent', now=5)


def test_memory_is_bounded(monkeypatch):
    monkeypatch.setattr(throttle, 'MAX_IDENTIFIERS', 2)
    for name in ('a', 'b', 'c'):
        throttle.record_failure(name, now=100)
    assert len(throttle._attempts) == 2
    assert 'a' not in throttle._attempts


class FakeQuery:
    def __init__(self, user): self.user = user
    def filter_by(self, **kwargs): return self
    def first(self): return self.user

class FakeDB:
    def __init__(self, user): self.user = user
    def query(self, model): return FakeQuery(self.user)


def test_login_bad_password_generic_and_locks(monkeypatch):
    monkeypatch.setattr(main.pwd, 'verify', lambda *args: False)
    user = SimpleNamespace(username='agent', password_hash='hash', is_active=True)
    for i in range(5):
        with pytest.raises(HTTPException) as error:
            main.login(SimpleNamespace(username='agent', password='wrong'), FakeDB(user))
        assert error.value.status_code == 401
        assert error.value.detail == 'Identifiants invalides'
    with pytest.raises(HTTPException) as error:
        main.login(SimpleNamespace(username='agent', password='wrong'), FakeDB(user))
    assert error.value.status_code == 429
    assert error.value.headers['Retry-After'] == '900'


def test_unknown_and_disabled_users_get_same_401(monkeypatch):
    monkeypatch.setattr(main.pwd, 'verify', lambda *args: False)
    for user in (None, SimpleNamespace(is_active=False, password_hash='hash')):
        with pytest.raises(HTTPException) as error:
            main.login(SimpleNamespace(username='unknown', password='wrong'), FakeDB(user))
        assert error.value.status_code == 401
        assert error.value.detail == 'Identifiants invalides'


def test_login_success_resets_counter(monkeypatch):
    monkeypatch.setattr(main.pwd, 'verify', lambda *args: True)
    monkeypatch.setattr(main, 'audit', lambda *args: None)
    monkeypatch.setattr(main, 'token', lambda *args: 'test-token')
    user = SimpleNamespace(username='agent', password_hash='hash', is_active=True, role=SimpleNamespace(value='AGENT'))
    for i in range(3): throttle.record_failure('agent')
    result = main.login(SimpleNamespace(username='agent', password='correct'), FakeDB(user))
    assert result['access_token'] == 'test-token'
    assert 'agent' not in throttle._attempts

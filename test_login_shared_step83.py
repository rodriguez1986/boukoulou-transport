"""Tests sans serveur Redis externe, étape 83."""
from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app import login_throttle_shared_step83 as shared
from app import main


class FakeRedis:
    def __init__(self): self.counts = {}
    def get(self, key): return self.counts.get(key)
    def eval(self, script, nkeys, key, window):
        assert 'INCR' in script and 'EXPIRE' in script
        assert nkeys == 1 and window == 900
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]
    def delete(self, key): self.counts.pop(key, None)


def request(ip, client):
    return SimpleNamespace(client=SimpleNamespace(host=ip), app=SimpleNamespace(state=SimpleNamespace(login_redis=client)))


def test_separate_network_addresses_do_not_lock_each_other():
    client = FakeRedis()
    a, b = request('192.0.2.10', client), request('192.0.2.11', client)
    for _ in range(5): shared.record_failure(client, ' Agent ', a)
    assert shared.is_blocked(client, 'agent', a)
    assert not shared.is_blocked(client, 'agent', b)
    assert not shared.is_blocked(client, 'other', a)
    assert 'Agent' not in str(client.counts)


def test_success_only_clears_current_bucket():
    client = FakeRedis()
    a, b = request('192.0.2.10', client), request('192.0.2.11', client)
    for _ in range(5):
        shared.record_failure(client, 'agent', a)
        shared.record_failure(client, 'agent', b)
    shared.clear_failures(client, 'agent', a)
    assert not shared.is_blocked(client, 'agent', a)
    assert shared.is_blocked(client, 'agent', b)


def test_untrusted_forwarded_header_is_ignored():
    client = FakeRedis()
    a = request('192.0.2.10', client)
    a.headers = {'X-Forwarded-For': '203.0.113.20'}
    assert shared._redis_key('agent', a) == shared._redis_key('agent', request('192.0.2.10', client))


def test_bad_config_fails_safely(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_LOGIN_REDIS_URL', 'https://example.invalid')
    with pytest.raises(RuntimeError, match='LOGIN_THROTTLE_CONFIG_INVALID'):
        shared.validate_redis_config()


def test_unavailable_backend_fails_closed():
    with pytest.raises(RuntimeError, match='LOGIN_THROTTLE_BACKEND_UNAVAILABLE'):
        shared.record_failure(None, 'agent', request('192.0.2.10', None))


def test_login_shared_mode_returns_503_when_backend_unavailable(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_LOGIN_REDIS_URL', 'redis://127.0.0.1:6379/0')
    with pytest.raises(HTTPException) as error:
        main.login(SimpleNamespace(username='agent', password='bad'), None, request('192.0.2.10', None))
    assert error.value.status_code == 503
    assert 'redis' not in str(error.value.detail).lower()

from types import SimpleNamespace
import pytest
from app import login_ip_step84 as ip
from app import login_throttle_shared_step83 as shared


def request(addr, headers=None):
    return SimpleNamespace(client=SimpleNamespace(host=addr), headers=headers or {})


class FakeRedis:
    def __init__(self): self.counts = {}
    def get(self, key): return self.counts.get(key)
    def eval(self, script, nkeys, key, window):
        assert nkeys == 1 and window == 900
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]


def test_ip_limit_across_multiple_usernames():
    ip._attempts.clear()
    a = request('192.0.2.1')
    for n in range(19):
        assert not ip.record_failure(a, now=100 + n)
    assert ip.record_failure(a, now=120)
    assert ip.is_blocked(a, now=121)
    assert not ip.is_blocked(request('192.0.2.2'), now=121)


def test_ip_window_expires():
    ip._attempts.clear()
    a = request('192.0.2.3')
    for _ in range(20): ip.record_failure(a, now=100)
    assert not ip.is_blocked(a, now=100 + 900)


def test_forwarded_header_does_not_change_ip():
    a = request('192.0.2.4', {'X-Forwarded-For': '192.0.2.5'})
    b = request('192.0.2.4')
    assert ip._redis_key(a) == ip._redis_key(b)


def test_redis_ip_limit_shared_across_accounts():
    redis = FakeRedis()
    a = request('192.0.2.6')
    for _ in range(20): ip.redis_record_failure(redis, a)
    assert ip.redis_is_blocked(redis, a)
    assert not ip.redis_is_blocked(redis, request('192.0.2.7'))
    assert '192.0.2.6' not in str(redis.counts)


def test_redis_unavailable_fails_closed():
    with pytest.raises(RuntimeError, match='LOGIN_THROTTLE_BACKEND_UNAVAILABLE'):
        ip.redis_is_blocked(None, request('192.0.2.8'))

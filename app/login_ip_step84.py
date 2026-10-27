"""Limite complémentaire des échecs de connexion par adresse réseau.

Les réussites ne remettent pas à zéro le compteur IP (anti password-spraying).
En mode multi-worker, utiliser le backend Redis partagé.
"""
import hashlib
import threading
import time
from collections import OrderedDict
from .login_throttle_shared_step83 import _client_address

IP_MAX_FAILURES = 20
IP_WINDOW_SECONDS = 900
IP_MAX_BUCKETS = 10000
_lock = threading.Lock()
_attempts = OrderedDict()


def _key(request):
    return _client_address(request)


def is_blocked(request, now=None):
    now = time.monotonic() if now is None else now
    with _lock:
        record = _attempts.get(_key(request))
        if not record:
            return False
        count, started = record
        if now - started >= IP_WINDOW_SECONDS:
            _attempts.pop(_key(request), None)
            return False
        return count >= IP_MAX_FAILURES


def record_failure(request, now=None):
    now = time.monotonic() if now is None else now
    with _lock:
        key = _key(request)
        count, started = _attempts.get(key, (0, now))
        if now - started >= IP_WINDOW_SECONDS:
            count, started = 0, now
        count += 1
        _attempts[key] = (count, started)
        _attempts.move_to_end(key)
        while len(_attempts) > IP_MAX_BUCKETS:
            _attempts.popitem(last=False)
        return count >= IP_MAX_FAILURES


def _redis_key(request):
    digest = hashlib.sha256(_key(request).encode('utf-8')).hexdigest()
    return 'boukoulou:login:ip:v1:' + digest


def redis_is_blocked(client, request):
    try:
        return int(client.get(_redis_key(request)) or 0) >= IP_MAX_FAILURES
    except Exception:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None


def redis_record_failure(client, request):
    from .login_throttle_shared_step83 import SCRIPT
    try:
        return int(client.eval(SCRIPT, 1, _redis_key(request), IP_WINDOW_SECONDS)) >= IP_MAX_FAILURES
    except Exception:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None

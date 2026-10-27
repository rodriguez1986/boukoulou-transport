"""Protection locale et bornée des tentatives de connexion (étape 82).

Limite par identifiant normalisé; pas de mot de passe ni de jeton stocké.
Pour plusieurs workers/instances, remplacer par un magasin atomique partagé.
"""
import threading
import time
from collections import OrderedDict

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60
LOCK_SECONDS = 15 * 60
MAX_IDENTIFIERS = 10_000
_lock = threading.Lock()
_attempts = OrderedDict()


def _key(username):
    return username.strip().casefold()[:80]


def is_blocked(username, now=None):
    now = time.monotonic() if now is None else now
    key = _key(username)
    with _lock:
        record = _attempts.get(key)
        if not record:
            return False
        count, started, blocked_until = record
        if blocked_until > now:
            return True
        if blocked_until or now - started >= WINDOW_SECONDS:
            _attempts.pop(key, None)
        return False


def record_failure(username, now=None):
    now = time.monotonic() if now is None else now
    key = _key(username)
    with _lock:
        record = _attempts.get(key)
        if record and record[2] > now:
            return True
        if not record or record[2] or now - record[1] >= WINDOW_SECONDS:
            count, started = 0, now
        else:
            count, started = record[0], record[1]
        count += 1
        blocked_until = now + LOCK_SECONDS if count >= MAX_FAILURES else 0
        _attempts[key] = (count, started, blocked_until)
        _attempts.move_to_end(key)
        while len(_attempts) > MAX_IDENTIFIERS:
            _attempts.popitem(last=False)
        return blocked_until > now


def clear_failures(username):
    with _lock:
        _attempts.pop(_key(username), None)

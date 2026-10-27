"""Registre local borné des alertes d'authentification (non persistant)."""
from collections import deque
from datetime import datetime, timezone
from threading import Lock

MAX_ALERTS = 200
_lock = Lock()
_alerts = deque(maxlen=MAX_ALERTS)
_sequence = 0
VALID_SCOPES = ('user_ref', 'client_ref')


def record(alert):
    """N'accepte que les champs attendus, jamais les données d'authentification brutes."""
    global _sequence
    allowed = ('event', 'component', 'scope', 'ref', 'count', 'window_seconds')
    safe = {key: alert[key] for key in allowed if key in alert}
    if safe.get('event') != 'login_failure_burst' or safe.get('scope') not in VALID_SCOPES:
        return
    with _lock:
        _sequence += 1
        _alerts.append({'id': _sequence, 'occurred_at': datetime.now(timezone.utc).isoformat(), **safe})


def recent(limit=50, *, scope=None, since=None, until=None, before_id=None):
    """Filtres combinables, ordre décroissant, borne de résultats après filtrage."""
    limit = max(1, min(int(limit), MAX_ALERTS))
    if scope is not None and scope not in VALID_SCOPES:
        raise ValueError('Portée inconnue')
    if since is not None and (since.tzinfo is None or since.utcoffset() is None):
        raise ValueError('since doit inclure un fuseau horaire')
    if until is not None and (until.tzinfo is None or until.utcoffset() is None):
        raise ValueError('until doit inclure un fuseau horaire')
    if since is not None and until is not None and since > until:
        raise ValueError('since doit précéder until')
    if before_id is not None and before_id < 1:
        raise ValueError('before_id doit être positif')
    with _lock:
        snapshot = list(reversed(_alerts))
    result = []
    for item in snapshot:
        if scope is not None and item['scope'] != scope:
            continue
        if before_id is not None and item['id'] >= before_id:
            continue
        if since is not None or until is not None:
            occurred = datetime.fromisoformat(item['occurred_at'])
            if since is not None and occurred < since:
                continue
            if until is not None and occurred > until:
                continue
        result.append(dict(item))
        if len(result) >= limit:
            break
    return result


def reset_for_tests():
    global _sequence
    with _lock:
        _alerts.clear()
        _sequence = 0

"""Détection locale des rafales d'échecs d'authentification (sans données brutes).

Les alertes sont des événements de journalisation, non des notifications garanties.
Chaque processus possède ses propres compteurs ; utiliser un SIEM partagé en production.
"""
from collections import deque
from threading import Lock
import logging
import json
import time

WINDOW_SECONDS = 300
THRESHOLD = 10
COOLDOWN_SECONDS = 300
MAX_KEYS = 4096
_lock = Lock()
_events = {}
_last_alert = {}
logger = logging.getLogger('boukoulou.security.alert')


def observe(event, user_ref=None, client_ref=None, now=None):
    """Retourne True si une nouvelle alerte est émise."""
    if event != 'login_failed':
        return False
    now = time.monotonic() if now is None else now
    keys = [('user_ref', user_ref), ('client_ref', client_ref)]
    alerts = []
    with _lock:
        # Éviter une croissance sans limite sur les comptes/adresses inventés.
        if len(_events) >= MAX_KEYS:
            for key in list(_events):
                queue = _events[key]
                while queue and queue[0] <= now - WINDOW_SECONDS:
                    queue.popleft()
                if not queue:
                    _events.pop(key, None)
                    _last_alert.pop(key, None)
            if len(_events) >= MAX_KEYS:
                oldest = next(iter(_events))
                _events.pop(oldest, None)
                _last_alert.pop(oldest, None)
        for kind, ref in keys:
            if not ref:
                continue
            key = (kind, ref)
            queue = _events.setdefault(key, deque())
            while queue and queue[0] <= now - WINDOW_SECONDS:
                queue.popleft()
            queue.append(now)
            if len(queue) >= THRESHOLD and now - _last_alert.get(key, float('-inf')) >= COOLDOWN_SECONDS:
                _last_alert[key] = now
                alerts.append({'event': 'login_failure_burst', 'component': 'auth.login', 'scope': kind, 'ref': ref, 'count': len(queue), 'window_seconds': WINDOW_SECONDS})
    from .security_alert_registry_step87 import record
    from . import security_alert_storage_step89 as storage
    for alert in alerts:
        if storage.enabled():
            try:
                storage.store(alert)
            except Exception:
                # La connexion reste utilisable ; échec du stockage visible dans les logs.
                logger.exception('security_alert_storage_failed')
        else:
            record(alert)
        logger.warning(json.dumps(alert, sort_keys=True))
    return bool(alerts)


def reset_for_tests():
    with _lock:
        _events.clear()
        _last_alert.clear()

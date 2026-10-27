"""Événements de sécurité de connexion, sans identifiants ni IP en clair.

À acheminer vers une collecte de logs centralisée avec rétention et alertes.
"""
import hashlib
import json
import logging
import os

logger = logging.getLogger('boukoulou.security.login')
ALLOWED = frozenset({'login_failed', 'login_blocked', 'login_succeeded', 'login_backend_unavailable'})


def _digest(value):
    # HMAC keyed pseudonymisation: salt must be a dedicated stable secret in production.
    import hmac
    key = os.getenv('BOUKOULOU_LOGIN_AUDIT_KEY', '')
    if not key:
        return None  # no reversible / low-entropy unsalted account hashes
    return hmac.new(key.encode('utf-8'), value.encode('utf-8'), hashlib.sha256).hexdigest()[:24]


def emit(event, username=None, request=None, reason=None):
    if event not in ALLOWED:
        raise ValueError('Événement de sécurité inconnu')
    from .login_throttle_shared_step83 import _client_address
    payload = {'event': event, 'component': 'auth.login'}
    if username is not None:
        identity = _digest(username.strip().casefold())
        if identity is not None:
            payload['user_ref'] = identity
    if request is not None:
        address = _digest(_client_address(request))
        if address is not None:
            payload['client_ref'] = address
    if reason in ('identifier_limit', 'ip_limit', 'backend_error', 'invalid_credentials'):
        payload['reason'] = reason
    logger.warning(json.dumps(payload, sort_keys=True))
    # Détection complémentaire sans bloquer ni modifier la réponse HTTP.
    if event == "login_failed":
        from .login_alert_step86 import observe
        observe(event, payload.get("user_ref"), payload.get("client_ref"))

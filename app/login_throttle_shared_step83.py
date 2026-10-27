"""Limiteur Redis atomique optionnel pour plusieurs workers (étape 83).

La clé combine un identifiant normalisé et l'adresse réseau du client ;
les échecs provenant d'autres adresses ne verrouillent pas globalement le compte.
Le mode Redis est fail-closed : une panne ne désactive pas la protection.
"""
import hashlib
import ipaddress
import os

from .login_throttle_step82 import MAX_FAILURES, LOCK_SECONDS, WINDOW_SECONDS, _key

SCRIPT = """
local n = redis.call('INCR', KEYS[1])
if n == 1 then redis.call('EXPIRE', KEYS[1], ARGV[1]) end
return n
"""


def redis_url():
    return os.getenv('BOUKOULOU_LOGIN_REDIS_URL', '').strip()


def validate_redis_config():
    url = redis_url()
    if not url:
        return None
    if not url.startswith(('redis://', 'rediss://', 'unix://')):
        raise RuntimeError('LOGIN_THROTTLE_CONFIG_INVALID')
    try:
        import redis
        client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
    except Exception as exc:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None
    return client


def _client_address(request):
    # Ne jamais faire confiance à X-Forwarded-For sans proxy de confiance.
    host = getattr(getattr(request, 'client', None), 'host', None)
    if not host:
        return 'unknown'
    try:
        return str(ipaddress.ip_address(host))
    except ValueError:
        return 'unknown'


def _redis_key(username, request):
    identity = _key(username) + '\0' + _client_address(request)
    digest = hashlib.sha256(identity.encode('utf-8')).hexdigest()
    return 'boukoulou:login:v1:' + digest


def _backend(client):
    if client is None:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE')
    return client


def is_blocked(client, username, request):
    try:
        return int(_backend(client).get(_redis_key(username, request)) or 0) >= MAX_FAILURES
    except Exception:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None


def record_failure(client, username, request):
    try:
        key = _redis_key(username, request)
        # Un compteur avec TTL borné, INCR + EXPIRE atomiques via Lua.
        count = int(_backend(client).eval(SCRIPT, 1, key, WINDOW_SECONDS))
        return count >= MAX_FAILURES
    except Exception:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None


def clear_failures(client, username, request):
    try:
        _backend(client).delete(_redis_key(username, request))
    except Exception:
        raise RuntimeError('LOGIN_THROTTLE_BACKEND_UNAVAILABLE') from None

"""Contrôles fail-closed de configuration au démarrage (aucune écriture)."""
import os
from .jwt_config_step63 import get_jwt_secret

VALID_ENVIRONMENTS = frozenset({'development', 'test', 'staging', 'production'})


def validate_startup_config(env=None):
    source = os.environ if env is None else env
    primary = str(source.get('BOUKOULOU_ENV', '')).strip().lower()
    secondary = str(source.get('APP_ENV', '')).strip().lower()
    if primary and primary not in VALID_ENVIRONMENTS:
        raise RuntimeError('BOUKOULOU_ENV inconnu')
    if secondary and secondary not in VALID_ENVIRONMENTS | {'prod'}:
        raise RuntimeError('APP_ENV inconnu')
    normalized_secondary = 'production' if secondary == 'prod' else secondary
    if primary and normalized_secondary and primary != normalized_secondary:
        raise RuntimeError('BOUKOULOU_ENV et APP_ENV contradictoires')
    mode = primary or normalized_secondary
    if mode == 'production':
        # Ne pas se fier au secret de développement éventuellement chargé à l'import.
        if source.get('BOUKOULOU_ENABLE_DEV_SEED') == '1':
            raise RuntimeError('Seed interdit : BOUKOULOU_ENV=development est obligatoire')
        get_jwt_secret({'APP_ENV': 'production', 'JWT_SECRET': source.get('JWT_SECRET')})
    return mode or 'unspecified'


def validate_loaded_jwt_secret(env=None, loaded_secret=None):
    """Fail closed si la clé JWT chargée à l'import diffère de la configuration active.

    Aucun secret n'est renvoyé ni journalisé. Ce contrôle doit précéder le seed.
    """
    import hmac
    source = os.environ if env is None else env
    expected = get_jwt_secret(source)
    if loaded_secret is None:
        from .security import SECRET
        loaded_secret = SECRET
    if not isinstance(loaded_secret, str) or not hmac.compare_digest(
        loaded_secret.encode('utf-8'), expected.encode('utf-8')
    ):
        raise RuntimeError('Clé JWT chargée incohérente avec la configuration active : redémarrage requis')
    return True

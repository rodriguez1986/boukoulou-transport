"""Validation de la durée de vie JWT, sans émission de jeton ni écriture."""
import os

DEFAULT_MINUTES = 480
PRODUCTION_MAX_MINUTES = 1440


def get_access_token_minutes(env=None):
    source = os.environ if env is None else env
    raw = source.get('ACCESS_TOKEN_MINUTES', str(DEFAULT_MINUTES))
    if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal():
        raise RuntimeError('ACCESS_TOKEN_MINUTES doit être un entier positif en minutes')
    minutes = int(raw)
    if minutes < 1:
        raise RuntimeError('ACCESS_TOKEN_MINUTES doit être strictement positif')
    primary = str(source.get('BOUKOULOU_ENV', '')).strip().lower()
    secondary = str(source.get('APP_ENV', '')).strip().lower()
    if (primary == 'production' or secondary in {'production', 'prod'}) and minutes > PRODUCTION_MAX_MINUTES:
        raise RuntimeError('ACCESS_TOKEN_MINUTES dépasse la limite de production (1440 minutes)')
    return minutes


def validate_loaded_access_token_minutes(env=None, loaded_minutes=None):
    """Empêche de démarrer avec une durée chargée différente de l'environnement."""
    expected = get_access_token_minutes(env)
    if loaded_minutes is None:
        from .security import MIN
        loaded_minutes = MIN
    if type(loaded_minutes) is not int or loaded_minutes != expected:
        raise RuntimeError('Durée JWT chargée incohérente : redémarrage requis')
    return True

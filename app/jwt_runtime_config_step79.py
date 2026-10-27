"""Vérification fail-closed des paramètres JWT réellement chargés à l'import.

Contrôle effectué avant le seed, sans exposer les secrets ni modifier l'environnement.
"""
from .startup_config_step68 import validate_loaded_jwt_secret
from .jwt_expiry_step71 import validate_loaded_access_token_minutes

EXPECTED_ALGORITHM = "HS256"
EXPECTED_CLOCK_SKEW_SECONDS = 5


def validate_loaded_jwt_runtime_config(env=None, *, secret=None, minutes=None,
                                       algorithm=None, clock_skew_seconds=None):
    from . import security

    # Les arguments optionnels permettent de tester des configurations corrompues
    # sans modifier les constantes utilisées par l'application en production.
    loaded_secret = security.SECRET if secret is None else secret
    loaded_minutes = security.MIN if minutes is None else minutes
    loaded_algorithm = security.JWT_ALGORITHM if algorithm is None else algorithm
    loaded_skew = (security.JWT_CLOCK_SKEW_SECONDS if clock_skew_seconds is None
                   else clock_skew_seconds)

    validate_loaded_jwt_secret(env=env, loaded_secret=loaded_secret)
    validate_loaded_access_token_minutes(env=env, loaded_minutes=loaded_minutes)
    if type(loaded_algorithm) is not str or loaded_algorithm != EXPECTED_ALGORITHM:
        raise RuntimeError("Algorithme JWT chargé incohérent : redémarrage requis")
    if type(loaded_skew) is not int or loaded_skew != EXPECTED_CLOCK_SKEW_SECONDS:
        raise RuntimeError("Tolérance d'horloge JWT chargée incohérente : redémarrage requis")
    return True

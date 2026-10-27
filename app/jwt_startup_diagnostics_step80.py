"""Diagnostic sûr des erreurs JWT au démarrage, sans divulguer la configuration.

Ne journalise jamais l'exception d'origine (qui pourrait contenir un secret).
"""
import logging

LOGGER = logging.getLogger('boukoulou.security.startup')


def validate_jwt_startup_safely(validate_environment, validate_runtime, *, logger=None):
    """Échoue avant le seed et expose seulement un code diagnostic stable.

    Les erreurs inattendues sont également neutralisées. Le code n'inclut
    jamais le contenu des variables d'environnement ou des exceptions.
    """
    log = LOGGER if logger is None else logger
    for code, check in (
        ('JWT_ENV_INVALID', validate_environment),
        ('JWT_RUNTIME_INVALID', validate_runtime),
    ):
        try:
            check()
        except Exception:
            log.error('Démarrage interrompu : %s', code)
            raise RuntimeError('Configuration de sécurité invalide (' + code + ')') from None
    return True

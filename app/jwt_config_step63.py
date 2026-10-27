"""Configuration JWT stricte en production, sans rotation automatique des clés."""
import os
import warnings
import re

# Valeur publique de développement, jamais un secret de production.
DEV_ONLY_SECRET = "boukoulou-dev-only-insecure-key-not-for-production-2026"
PLACEHOLDERS = frozenset({"dev-secret", "CHANGE_THIS_SECRET", "CHANGE_THIS_IN_PRODUCTION", "changeme", "secret"})


# Marqueurs explicites de modèles et de valeurs factices, y compris dans
# des chaînes suffisamment longues pour franchir le seuil de 32 octets.
_UNSAFE_MARKERS = (
    'change_this', 'changeme', 'change-me', 'replace_me', 'replace-me',
    'replace_this', 'your-secret', 'your_secret', 'your-jwt', 'your_jwt',
    'placeholder', 'example-secret', 'example_secret',
    'dummy-secret', 'dummy_secret', 'default-secret', 'default_secret',
    'dev-only', 'development-only', 'not-for-production',
)


def is_unsafe_production_secret(secret):
    """Détecte des valeurs de démonstration sans exposer la clé dans les erreurs."""
    if not isinstance(secret, str):
        return True
    normalized = secret.strip().lower()
    if not normalized or normalized != secret.lower():
        return True
    if normalized in {item.lower() for item in PLACEHOLDERS}:
        return True
    if any(marker in normalized for marker in _UNSAFE_MARKERS):
        return True
    # Une longue répétition d'un caractère ne constitue pas une clé robuste.
    if len(set(normalized)) <= 2:
        return True
    # Exemples typiques : 1234567890 répété ou abcdef répété.
    if re.fullmatch(r'(?:0123456789|123456789|abcdefghijklmnopqrstuvwxyz|abcdef){2,}', normalized):
        return True
    return False


def get_jwt_secret(env=None):
    """Lit JWT_SECRET et refuse toute clé absente/faible en environnement production.

    Aucun secret de production n'est généré ou modifié automatiquement.
    """
    source = os.environ if env is None else env
    mode = str(source.get("APP_ENV", "development")).strip().lower()
    raw = source.get("JWT_SECRET")
    secret = raw if raw is not None else DEV_ONLY_SECRET
    if mode in {"production", "prod"}:
        if raw is None or len(raw.encode("utf-8")) < 32 or is_unsafe_production_secret(raw) or raw == DEV_ONLY_SECRET:
            raise RuntimeError("JWT_SECRET doit être une clé robuste (>= 32 octets), non prédéfinie, en production")
    elif raw is not None and (len(raw.encode("utf-8")) < 32 or raw in PLACEHOLDERS):
        warnings.warn("JWT_SECRET trop court ou prédéfini : usage développement seulement", RuntimeWarning, stacklevel=2)
    return secret

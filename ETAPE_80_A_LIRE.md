# Boukoulou Transport V5.9 — Étape 80

## Objectif
Empêcher les fuites d'informations sensibles lors d'une erreur de configuration JWT au démarrage.

## Changements
- `app/jwt_startup_diagnostics_step80.py` : exécute les validations d'environnement puis de configuration JWT, avec arrêt immédiat au premier échec.
- Les messages et logs d'échec contiennent uniquement les codes `JWT_ENV_INVALID` ou `JWT_RUNTIME_INVALID`, jamais la valeur de l'exception d'origine, une clé JWT ou des paramètres d'environnement.
- `app/main.py` : utilise cette vérification au début du lifespan, avant `seed()`.
- `test_jwt_startup_diagnostics_step80.py` : vérifie les cas valides, les erreurs attendues/inattendues, l'absence de divulgation et l'interdiction du seed en cas d'échec.
- Les tests historiques de démarrage sont adaptés aux nouveaux messages de diagnostic publics, sans modifier les règles de sécurité sous-jacentes.

## Vérification
`python -m pytest -q` : 735 réussis, 12 ignorés.

## Limites
La vérification se produit au démarrage, pas en continu. Les diagnostics sont volontairement peu détaillés : vérifier la configuration par un canal d'administration sécurisé si nécessaire. Aucune migration, rotation de secret ou opération de production n'a été effectuée.

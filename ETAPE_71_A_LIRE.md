# Boukoulou Transport V5.9 — Étape 71

## Objectif
Valider la durée de validité JWT et empêcher un décalage entre configuration active et valeur chargée.

## Changements
- `app/jwt_expiry_step71.py` : parsing strict des minutes, valeur par défaut 480, durée strictement positive, limite de production de 1440 minutes.
- `app/security.py` : la constante `MIN` utilise la validation centralisée.
- `app/main.py` : vérification de cohérence de la durée chargée au démarrage, avant le seed.
- `test_jwt_expiry_step71.py` : 18 tests supplémentaires.

## Tests
`python -m pytest -q` : **621 passed, 12 skipped**.

## Limites
La limite de 24 heures est une règle de sécurité de cette étape et peut nécessiter un ajustement métier. Les jetons déjà émis ne sont pas révoqués par ce contrôle. Aucun déploiement, rotation de secret, migration ou opération sur une base de production. Les tests PostgreSQL externes restent ignorés.

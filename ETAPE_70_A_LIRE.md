# Boukoulou Transport V5.9 — Étape 70

## Objectif
Refuser en production les clés JWT manifestement factices même si elles dépassent 32 octets.

## Changements
- `app/jwt_config_step63.py` : fonction `is_unsafe_production_secret` détectant des marqueurs de configuration fictive (placeholder, change-this, replace-me, example-secret, etc.) et des répétitions évidentes.
- `get_jwt_secret` refuse ces clés en production, sans afficher la valeur de la clé.
- `test_jwt_placeholder_step70.py` : 13 tests de non-régression.

## Vérification
`python -m pytest -q` : **603 passed, 12 skipped**.

## Limites
La détection de valeurs factices ne mesure pas l'entropie cryptographique. Utiliser un secret réellement aléatoire, géré par un gestionnaire de secrets. Aucune rotation de secret, migration, ni mise en production n'a été réalisée. Les tests PostgreSQL nécessitant une infrastructure externe restent ignorés dans cette exécution.

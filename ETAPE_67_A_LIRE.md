# Étape 67 — Séparation des environnements et protection du seed

## Reconstitution
Projet complet issu de l'étape 66, conservant les étapes antérieures.

## Modifications
- `app/main.py` : le seed nécessite simultanément `BOUKOULOU_ENABLE_DEV_SEED=1` et `BOUKOULOU_ENV=development` (insensible à la casse pour le nom d'environnement). Hors développement, l'application refuse le seed avant toute ouverture de session.
- `test_environment_step67.py` : 10 tests supplémentaires vérifiant l'interdiction du seed en production/test/staging/sans environnement, le démarrage sans seed et le seed explicite de développement.
- `test_lifespan_step65.py`, `test_lifespan_step66.py` : les tests de seed déclarent maintenant explicitement l'environnement développement.

## Tests
`python -m pytest -q` : 571 réussis, 12 ignorés, 0 échec.

## Configuration
- Production : `BOUKOULOU_ENV=production` et `BOUKOULOU_ENABLE_DEV_SEED=0` (ou variable absente).
- Test : `BOUKOULOU_ENV=test` et seed désactivé.
- Développement : `BOUKOULOU_ENV=development`; pour autoriser le seed, ajouter explicitement `BOUKOULOU_ENABLE_DEV_SEED=1`.
- Si le seed est demandé hors développement, le démarrage échoue volontairement.

## Limites
Les tests sont locaux, sans PostgreSQL de production ni intégration de paiement réel. Aucun secret, aucune migration et aucun déploiement n'ont été modifiés.

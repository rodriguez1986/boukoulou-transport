# Étape 56 — Éviter les affectations simultanées sur plusieurs voyages

## Reconstitution
Les étapes 1–55 sont conservées. Les routes d'affectation restent non montées.

## Amélioration
`attribuer()` verrouille la ligne `User` de l'employé avant la ligne `Trip`, puis compare les intervalles actifs de **tous ses voyages**. Un employé ne peut plus être affecté simultanément à deux voyages, même différents. Les périodes adjacentes [début, fin) sont autorisées ; les périodes ouvertes bloquent les affectations ultérieures.

Tests : `python -m pytest -q test_crew_cross_trip_step56.py test_crew_assignment_admin_step49.py test_crew_concurrency_step55.py`.

## Limites
SQLite n'applique pas `FOR UPDATE` : la sûreté concurrente PostgreSQL doit être testée sur une base isolée avant production. Aucune migration ni activation des routes n'a été effectuée. Les affectations déjà présentes dans une base réelle devront être auditées pour les conflits entre voyages avant déploiement.

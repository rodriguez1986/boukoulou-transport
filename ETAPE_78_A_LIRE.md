# Boukoulou Transport V5.9 — Étape 78

## Objectif
Tolérer les petits écarts d'horloge sur les dates JWT `iat` et `nbf` sans prolonger l'expiration `exp`.

## Modifications
- `app/security.py` : `JWT_CLOCK_SKEW_SECONDS = 5`. La validation automatique PyJWT de `iat` et `nbf` est remplacée par une validation explicite stricte des types, de la chronologie et de la limite de 5 secondes d'avance. La validation automatique de `exp` reste active et sans tolérance.
- `test_jwt_clock_skew_step78.py` : dix tests couvrant les écarts de 1, 3, 5, 6, 30 et 3600 secondes, l'expiration stricte, les anciens jetons et les champs temporels incomplets.

## Limites
Tolérance fixe de cinq secondes, non destinée à compenser une mauvaise synchronisation NTP. La durée de vie signée maximale reste inchangée. Aucun déploiement, migration ni rotation de secret n'a été effectué.

## Vérification
`python -m pytest -q` : 706 tests réussis, 12 ignorés.

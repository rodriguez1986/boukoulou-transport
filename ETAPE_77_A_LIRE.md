# Boukoulou Transport V5.9 — Étape 77

## Objectif
Renforcer la cohérence temporelle JWT et couvrir les limites exactes de validité.

## Modifications
- `app/security.py` : impose, pour les jetons possédant `iat` et `nbf`, `iat <= nbf < exp` ; le contrôle existant `exp - iat <= MIN * 60` reste strict.
- `test_jwt_boundaries_step77.py` : huit tests de frontière (durée exactement maximale, dépassement d'une seconde, ordre des dates, égalités et compatibilité historique).

## Compatibilité et limites
Les jetons historiques sans `iat` ni `nbf` restent acceptés jusqu'à leur expiration, sous réserve des autres contrôles. La validité à l'instant présent continue d'être vérifiée par PyJWT. Aucun déploiement, rotation de secret ou migration de base de données.

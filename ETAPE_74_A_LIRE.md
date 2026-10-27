# Boukoulou Transport V5.9 — Étape 74

## Objectif
Refuser les JWT dont la durée de vie réelle excède la durée autorisée, même si la date d'expiration reste valide.

## Modifications
- `app/security.py` : pour les JWT contenant `iat` et `nbf`, vérifie que `exp - iat` et `exp - nbf` n'excèdent pas `MIN * 60` secondes.
- `test_jwt_lifetime_step74.py` : 6 tests de durée maximale, durée excessive, date d'expiration proche, jeton historique et émission.
- Aucun secret JWT n'est affiché dans les messages d'erreur.

## Vérification
`python -m pytest -q` : 673 passed, 12 skipped. Tests locaux uniquement.

## Limites
Les anciens JWT sans `iat` et `nbf` restent acceptés jusqu'à expiration, sous réserve des autres contrôles. Ils ne peuvent pas faire l'objet d'un contrôle de durée de vie réelle faute de date d'émission. Aucun déploiement, migration ou rotation de clé.

# Boukoulou Transport V5.9 — Étape 72

## Objectif
Renforcer les contrôles des champs JWT à la réception des requêtes authentifiées.

## Modifications
- `app/security.py` : PyJWT exige explicitement `sub`, `tv`, `exp` ; `sub` doit être une chaîne décimale ASCII représentant un identifiant positif ; `tv` est un entier positif ou nul non booléen ; `exp` doit être un entier positif non booléen et sa validité temporelle reste contrôlée par PyJWT.
- `test_jwt_claims_step72.py` : tests HTTP pour champs absents, types invalides, expiration et jeton valide.

## Vérification
`python -m pytest -q` : 647 passed, 12 skipped. Tests exécutés localement ; aucun test PostgreSQL externe n'a été activé.

## Limites
Les JWT déjà émis restent valides jusqu'à leur expiration s'ils satisfont les nouvelles règles. Les paramètres de rotation des clés, les algorithmes alternatifs et les mécanismes de révocation externes ne sont pas ajoutés. Aucun déploiement, aucune migration ni modification de secret réel.

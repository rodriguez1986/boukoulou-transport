# Boukoulou Transport V5.9 — Étape 73

## Objectif
Renforcer les contrôles temporels des jetons JWT.

## Modifications
- `app/security.py` : les nouveaux jetons incluent `iat` et `nbf` au même instant UTC que leur émission.
- À la vérification, les champs `iat` et `nbf`, s'ils sont présents, doivent être des timestamps Unix entiers strictement positifs (pas de booléens, chaînes ou flottants), antérieurs ou égaux à `exp` ; `iat` ne peut dépasser `nbf` quand les deux sont présents.
- PyJWT continue à refuser les jetons non encore valides (`nbf` futur) et ceux émis dans le futur (`iat` futur).
- Compatibilité conservée pour les jetons précédemment émis sans `iat`/`nbf`, jusqu'à expiration.
- `test_jwt_time_step73.py` : tests de sécurité et d'émission.

## Vérification
`python -m pytest -q` : 667 passed, 12 skipped. Tests locaux uniquement.

## Limites
Aucune rotation de clé, migration, connexion à un service externe ni déploiement. Les anciens jetons sans iat/nbf sont volontairement compatibles. Une tolérance d'horloge n'a pas été introduite.

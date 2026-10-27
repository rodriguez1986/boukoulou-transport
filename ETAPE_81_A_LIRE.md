# Boukoulou Transport V5.9 — Étape 81

## Objectif
Uniformiser les réponses HTTP d'authentification sans révéler de détails sensibles.

## Modifications
- `app/security.py` : `HTTPBearer(auto_error=False)` sur les routes protégées pour traiter explicitement les jetons absents ou malformés en HTTP 401 au lieu d'une erreur de dépendance différente.
- En-tête `WWW-Authenticate: Bearer` sur les erreurs 401 liées aux JWT et aux sessions.
- `utilisateur_optionnel` : accès anonyme préservé sans Authorization ; en-tête invalide refusé en 401.
- `test_auth_http_step81.py` : tests HTTP couvrant l'absence d'en-tête, les schémas invalides, les jetons malformés, l'accès anonyme et les jetons valides.

## Validation
Commande exécutée : `PYTHONPATH=test_support_step53:. python -m pytest -q`
Résultat : 768 passed, 10 skipped.

Le répertoire `test_support_step53` contient une adaptation **réservée aux tests** et ne doit pas être ajouté au PYTHONPATH de production. Les intégrations externes nécessitent des validations dédiées avant mise en service.

Aucun déploiement, aucune migration et aucune rotation de secret réalisés.

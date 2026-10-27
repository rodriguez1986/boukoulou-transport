# Étape 88 — Filtres des alertes de connexion

La route `GET /admin/security/login-alerts`, accessible uniquement aux **ADMIN**, accepte désormais :

- `scope=user_ref` ou `scope=client_ref` (filtre par portée pseudonymisée) ;
- `since` et `until` (horodatages ISO 8601 avec fuseau obligatoire, bornes inclusives) ;
- `before_id` (pagination simple, ID strictement inférieur à la valeur indiquée) ;
- `limit` (entre 1 et 200, appliqué **après** les filtres).

Exemple : `/admin/security/login-alerts?scope=client_ref&limit=20&before_id=150`.

Les alertes restent triées par ID décroissant, limitées aux 200 plus récentes **par processus**, sans persistance ni agrégation multi-workers. Les paramètres invalides renvoient 422. Les références sont pseudonymisées ; ne pas y ajouter d'identifiants bruts. Aucune migration ni déploiement.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

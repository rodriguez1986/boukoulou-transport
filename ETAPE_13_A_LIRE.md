# Étape 13 — Tests HTTP de la caisse

Cette étape ajoute `test_cash_api_step13.py` :
- 4 tests statiques sur les routes, les rôles, les conflits HTTP 409 et les contrôles de propriété ;
- 2 tests HTTP FastAPI utilisant `TestClient` et des dépendances simulées, sans toucher PostgreSQL.

Les tests HTTP nécessitent les dépendances du `requirements.txt`. Ils vérifient
les réponses 409 (caisse déjà ouverte) et 403 (rôle interdit) sur la route
`POST /cash/sessions/open`. Le scénario de conflit SQL concurrent (409)
nécessite toujours des tests d'intégration PostgreSQL supplémentaires.

Pour lancer dans un environnement de test correctement configuré :
`python -m pytest -q test_cash_api_step13.py`

Ne pas déployer en production. Ne pas lancer les migrations sur une base réelle.
Les modules reconstitués n'ont pas encore été validés de bout en bout.

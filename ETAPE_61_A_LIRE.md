# Étape 61 — Tests HTTP/JWT complets de l'API administrative des anomalies

## Reconstitution
Tous les fichiers des étapes 1 à 60 sont conservés.

## Amélioration
- `test_crew_assignment_report_http_step61.py` : 16 tests HTTP avec FastAPI TestClient et SQLite en mémoire isolée.
- JWT absent, signature invalide, expiration, compte désactivé, révocation par token_version.
- ADMIN global, COUNTRY_MANAGER limité à son pays, autres rôles refusés.
- Pagination, paramètres invalides (422), absence de modification des affectations et audits.
- Le routeur étape 60 reste NON monté dans `app/main.py`.

## Commandes
```bash
python -m pytest -q test_crew_assignment_report_http_step61.py
python -m pytest -q --ignore=test_security_step6.py
```

## Précautions
- SQLite en mémoire ne valide pas le comportement concurrent PostgreSQL : essais sur PostgreSQL requis avant activation.
- Le shim `test_support_step53/passlib` est UNIQUEMENT destiné aux tests. Ne jamais l'ajouter au PYTHONPATH de production.
- La clé JWT de développement `dev-secret` doit être remplacée par une clé secrète robuste en production.
- Le routeur n'est pas activé en production et aucune migration ni opération de paiement n'est exécutée.

## Résultats de vérification
- Nouveaux tests HTTP : **16 réussis**.
- Suite compatible : **498 réussis, 12 ignorés**, commande :
  `python -m pytest -q --ignore=test_security_step6.py --ignore=test_payment_api_step45.py`.
- **Limitation connue** : si `test_payment_api_step45.py` est collecté avant les tests JWT, il injecte un substitut d'authentification dans le routeur de paiement (effet de bord historique) : 12 tests JWT de paiement échouent alors. Le fichier est donc exclu de cette exécution globale, mais n'a pas été supprimé. Ce conflit de collecte doit être corrigé dans une prochaine étape.

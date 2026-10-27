# Étape 19 — Contrôles HTTP JWT et permissions de caisse

Cette étape ajoute six scénarios HTTP réels utilisant `TestClient` sur l'application FastAPI :

1. JWT valide pour un utilisateur DRIVER : `GET /auth/me` → 200.
2. Même utilisateur DRIVER : `POST /cash/sessions/open` → 403.
3. JWT avec ancienne `token_version` → 401.
4. JWT expiré → 401.
5. Utilisateur désactivé → 401.
6. Utilisateur inexistant → 401.

**Isolation :** URL SQLite en mémoire, `get_db` remplacé par un faux dépôt utilisateur, amorçage désactivé. Aucune table créée ni migration lancée. Les scénarios ne valident **pas** la logique métier d'ouverture de caisse ni la concurrence PostgreSQL.

## Exécution sur Windows

Extraire l'archive dans un nouveau dossier de développement. Depuis PowerShell, dans ce dossier :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\tester_auth_etape19.ps1
```

Ce script nécessite Python 3 et une connexion Internet pour installer les dépendances dans `.venv`. Si une erreur survient, conserver la sortie complète. Ne pas exécuter sur un environnement de production.

## Validation lors de la préparation

Les tests statiques ont été exécutés ; les scénarios HTTP réels restent à confirmer sur un environnement disposant des dépendances complètes.

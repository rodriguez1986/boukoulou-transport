# Étape 18 — Premiers appels HTTP isolés

Cette étape ajoute un smoke test utilisant **le vrai objet FastAPI** avec
`fastapi.testclient.TestClient` :

- `GET /health` → HTTP 200 et `{"status":"ok"}` ;
- `GET /auth/me` avec un JWT volontairement invalide → HTTP 401 ;
- `POST /cash/sessions/open` avec le même JWT invalide → HTTP 401.

La connexion est forcée vers **SQLite en mémoire** et l'amorçage des données
est désactivé **avant l'import de l'application**. Aucune migration n'est
exécutée. Ce test ne valide **pas** les opérations de caisse authentifiées,
les règles métier sur PostgreSQL ni la concurrence.

## Exécution Windows (environnement de développement seulement)

1. Extraire toute l'archive dans un nouveau dossier.
2. Ouvrir PowerShell dans ce dossier.
3. Lancer :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\tester_http_etape18.ps1
```

4. Si une erreur apparaît, transmettre **la sortie complète** avant de
continuer. Le script installe les dépendances dans `.venv` et nécessite
Python 3 ainsi qu'une connexion Internet pour `pip`.

## État de validation

Les tests statiques ont été vérifiés dans l'environnement de préparation.
**Les appels HTTP réels n'ont pas encore été exécutés avec toutes les
dépendances installées** : leur résultat doit être confirmé sur Windows.

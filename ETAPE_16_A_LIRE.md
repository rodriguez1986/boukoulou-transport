# Étape 16 — Préparation du démarrage sécurisé de FastAPI

## Changements
- `app/main.py` : suppression de `Base.metadata.create_all(engine)` à l'import.
- Amorçage automatique (`seed`) désactivé par défaut ; il ne fonctionne que si
  `BOUKOULOU_ENABLE_DEV_SEED=1` est explicitement défini. **Ne pas l'activer
  sur une base de production**.
- `scripts/smoke_import_etape16.py` : essai d'import dans une base SQLite
  **en mémoire**, sans migration et sans démarrage de serveur.
- `test_startup_step16.py` : trois tests statiques des garde-fous.

## Sur Windows (dans le dossier extrait, après installation des dépendances)
```powershell
.\.venv\Scripts\python.exe -m pytest -q test_startup_step16.py
.\.venv\Scripts\python.exe scripts\smoke_import_etape16.py
```

L'essai d'import peut révéler d'autres incompatibilités de modèles ou de
bibliothèques : ne pas interpréter un échec comme une permission de lancer
les migrations. Le serveur complet, les tests HTTP et PostgreSQL restent à
valider. Aucun déploiement en production recommandé.

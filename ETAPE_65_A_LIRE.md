# Étape 65 — Migration FastAPI vers lifespan

## Reconstitution
Toutes les étapes précédentes jusqu'à l'étape 64 sont conservées.

## Modifications
- `app/main.py` : remplace `@app.on_event("startup")` par `lifespan` (`asynccontextmanager`).
- `seed()` reste explicitement désactivé sauf si `BOUKOULOU_ENABLE_DEV_SEED=1`.
- Aucune migration, création automatique de tables, paiement réel ou activation de route supplémentaire.
- `test_lifespan_step65.py` : tests du cycle de vie, du `/health`, de l'absence de connexion DB par défaut, du seed opt-in et de la fermeture de session.

## Vérification
`python -m pytest -q` — résultats à consulter dans le journal de tests joint si présent.

## Limites
Les tests PostgreSQL réels non configurés restent ignorés. Pas de déploiement en production.

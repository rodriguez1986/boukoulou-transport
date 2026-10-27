# Boukoulou Transport V5.9 — Étape 69

## Objectif
Empêcher le démarrage si la clé JWT chargée au moment de l'import de `app.security` ne correspond pas à `JWT_SECRET` de l'environnement actif.

## Modifications
- `app/startup_config_step68.py` : ajout de `validate_loaded_jwt_secret()` ; comparaison des clés avec `hmac.compare_digest` sans les afficher.
- `app/main.py` : contrôle après validation de la configuration, avant l'initialisation optionnelle des données.
- `test_loaded_jwt_step69.py` : six tests, y compris démarrage refusé avant seed et démarrage accepté si clé cohérente.
- Adaptation de deux fichiers de tests préexistants pour simuler une clé chargée cohérente lorsque l'environnement de test change pendant l'exécution.

## Résultats
`python -m pytest -q` : **590 passed, 12 skipped**.

## Limites et exploitation
- Aucun changement de secret ou rotation de clés automatique ; le changement d'une clé JWT exige un redémarrage complet du processus applicatif.
- Les tests n'impliquent pas un déploiement ni une validation de préproduction.
- L'environnement doit être fixé avant le démarrage de l'application.
- Le contrôle est exécuté lors du démarrage `lifespan` de FastAPI, pas à chaque requête.

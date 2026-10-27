# Étape 68 — Validation de configuration au démarrage

## Reconstitution
Projet complet de l'étape 67, avec tous les fichiers antérieurs.

## Modifications
- `app/startup_config_step68.py` : validation de `BOUKOULOU_ENV` et `APP_ENV`, détection des contradictions, interdiction du seed en production et contrôle de `JWT_SECRET` (au moins 32 octets et non prédéfini).
- `app/main.py` : validation avant l'appel à `seed()` et avant toute session d'initialisation.
- `test_startup_config_step68.py` : 13 tests de configuration et de démarrage.
- `test_environment_step67.py` : clé de test suffisamment robuste pour le scénario production sans seed.

## Tests
`python -m pytest -q` : 584 réussis, 12 ignorés, 0 échec.

## Configuration recommandée
Production : `BOUKOULOU_ENV=production`, `APP_ENV=production`, `JWT_SECRET=<clé robuste unique>`, `BOUKOULOU_ENABLE_DEV_SEED=0`.
Développement : `BOUKOULOU_ENV=development`, `APP_ENV=development`, seed explicitement activé uniquement si nécessaire.

## Limites
La validation est locale, sans PostgreSQL de production ni PSP réel. Une clé déjà chargée au moment de l'import de `app.security` n'est pas automatiquement remplacée si les variables d'environnement changent après cet import ; en déploiement, configurer les variables avant de lancer le processus. Le mode non déclaré est encore accepté pour compatibilité avec les tests et installations antérieurs. Aucun secret ni paiement réel n'a été modifié.

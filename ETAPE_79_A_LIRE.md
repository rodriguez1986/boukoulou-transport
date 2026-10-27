# Boukoulou Transport V5.9 — Étape 79

## Objectif
Assurer la cohérence de la configuration JWT entre émission, validation et démarrage.

## Modifications
- `app/security.py` : constante commune `JWT_ALGORITHM = "HS256"` utilisée pour l'émission et la validation ; les règles temporelles précédentes restent inchangées.
- `app/jwt_runtime_config_step79.py` : contrôle fail-closed du secret, de la durée de vie, de l'algorithme HS256 et de la tolérance d'horloge de 5 secondes chargés en mémoire.
- `app/main.py` : contrôle global effectué au début du lifespan, avant le seed.
- `test_jwt_runtime_config_step79.py` : tests de configuration cohérente et divergente, types inattendus et émission HS256.

## Limites
Cette vérification s'effectue au démarrage et ne surveille pas les changements d'environnement pendant l'exécution. Un redémarrage est nécessaire après toute modification de configuration. Aucune clé réelle n'est modifiée, aucune migration ni déploiement n'est réalisé.

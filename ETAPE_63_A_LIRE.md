# Étape 63 — Sécurisation de la configuration JWT

## Reconstitution
Tous les fichiers des étapes 1 à 62 sont conservés.

## Améliorations
- Nouvelle fonction `get_jwt_secret` dans `app/jwt_config_step63.py`.
- En `APP_ENV=production` ou `prod`, l'application refuse le démarrage si `JWT_SECRET` manque, fait moins de 32 octets ou correspond à une valeur d'exemple connue.
- En développement, une clé **publique, uniquement pour les tests** est utilisée si aucune variable n'est définie ; elle ne doit jamais servir en production.
- Le `docker-compose.yml` exige désormais `JWT_SECRET` depuis l'environnement (ou `.env`) au lieu d'une clé d'exemple intégrée.
- Tests des modes production/développement et de la configuration Compose.

## Déploiement (non effectué)
- Définir une valeur aléatoire secrète d'au moins 32 octets pour `JWT_SECRET` et `APP_ENV=production` dans l'environnement du service avant de démarrer.
- Conserver le secret de production existant si un déploiement utilise déjà des JWT ; changer le secret invalide les JWT existants et affecte les signatures QR.
- Ne jamais mettre une vraie clé dans Git, dans `.env.example` ou dans les archives.
- Les valeurs d'exemple `ADMIN_PASSWORD` et les identifiants PostgreSQL du Compose restent à sécuriser avant production.

## Limites
Aucun serveur PostgreSQL réel, aucun déploiement, aucune rotation de clé, aucune migration ni paiement réel.

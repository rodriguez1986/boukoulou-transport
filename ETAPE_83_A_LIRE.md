# Étape 83 — Limitation de connexion partagée Redis (optionnelle)

## Fonctionnement
- Sans `BOUKOULOU_LOGIN_REDIS_URL`, comportement local de l'étape 82 inchangé (5 échecs / 15 min, blocage temporaire).
- Avec `BOUKOULOU_LOGIN_REDIS_URL` (`redis://`, `rediss://` ou `unix://`), le serveur vérifie Redis au démarrage ; échec explicite et sans divulgation si indisponible.
- Les échecs sont comptabilisés dans Redis de façon atomique via script Lua (`INCR` + `EXPIRE`). Les clés sont des empreintes SHA-256 de l'identifiant normalisé et de l'adresse IP client ; ni mot de passe ni jeton n'est stocké.
- Le blocage porte sur le couple identifiant/adresse IP et évite le verrouillage global d'un compte par une autre IP. Les en-têtes `X-Forwarded-For` ne sont pas exploités directement.
- Une panne Redis pendant une requête de connexion provoque une réponse 503 générique : aucune désactivation silencieuse de la protection.

## Configuration
Installer `redis==5.2.1` depuis requirements.txt et définir `BOUKOULOU_LOGIN_REDIS_URL` sur les instances. Sécuriser les identifiants Redis et le transport (TLS en environnement distant). Configurer les proxies de confiance au niveau du serveur ASGI ; le code ne lit pas lui-même les en-têtes transmis.

## Limites
- Le TTL de 15 minutes commence au premier échec : le blocage n'est pas nécessairement de 15 minutes complètes après le cinquième échec. `Retry-After: 900` reste une indication maximale, non calculée.
- Un attaquant réparti sur de nombreuses IP peut continuer à essayer un compte ; prévoir aussi un plafond par IP/réseau, de la supervision, des alertes et une défense en périphérie.
- En l'absence de configuration Redis, le limiteur local n'est toujours pas partagé entre instances.
- Aucun service Redis réel n'a été démarré ou testé dans cette étape : tests unitaires avec un faux client Redis. Aucune modification de base de données ni déploiement.

## Tests
`PYTHONPATH="$PWD/test_support_step53:$PWD" python -m pytest -q`

Résultat : 781 passed, 10 skipped.

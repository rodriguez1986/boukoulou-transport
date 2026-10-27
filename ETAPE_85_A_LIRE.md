# Étape 85 — Journalisation de sécurité de la connexion

Les événements `login_failed`, `login_blocked`, `login_succeeded` et `login_backend_unavailable` sont consignés dans le logger `boukoulou.security.login` au format JSON. Aucun mot de passe, JWT, nom d'utilisateur ou IP en clair n'est journalisé par ce module.

Pour corréler les événements, configurer une clé dédiée et aléatoire `BOUKOULOU_LOGIN_AUDIT_KEY` (distincte de la clé JWT). Elle permet de générer des références pseudonymisées HMAC. Sans cette clé, les références utilisateur et IP sont omises. Ne pas placer la clé dans le dépôt. Centraliser les logs, définir une rétention, un contrôle d'accès et des alertes de sécurité. Aucune migration de base ni déploiement de collecte de logs n'est réalisé.

La journalisation n'est pas une garantie de livraison durable si le système de collecte est indisponible.

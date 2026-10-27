# Étape 87 — Consultation des alertes de sécurité

Route `GET /admin/security/login-alerts?limit=50` réservée au rôle **ADMIN** via la dépendance d'autorisation existante. Retourne les alertes `login_failure_burst` les plus récentes, avec `id`, horodatage UTC, portée, référence pseudonymisée, nombre d'échecs et fenêtre de détection. La réponse indique `scope: local_process` et `persistent: false`.

Le registre local est protégé par verrou et borné à **200 alertes par processus**. Le paramètre `limit` est limité à 1–200. Aucun mot de passe, JWT, IP ou nom d'utilisateur brut n'est conservé par ce registre. La génération de références pseudonymisées nécessite `BOUKOULOU_LOGIN_AUDIT_KEY` comme à l'étape 85.

**Important :** le registre n'est ni partagé entre workers ni durable après redémarrage. Il ne remplace pas un SIEM centralisé. Pas de migration de base de données ni de déploiement externe.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

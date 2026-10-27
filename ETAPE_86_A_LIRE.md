# Étape 86 — Détection de rafales de connexions suspectes

Le module `app/login_alert_step86.py` observe les événements `login_failed` émis par l'audit de l'étape 85. Il émet une alerte JSON `login_failure_burst` sur le logger `boukoulou.security.alert` après **10 échecs en 5 minutes** pour une même référence pseudonymisée d'utilisateur ou d'adresse client. Les alertes sont limitées à une par référence toutes les 5 minutes. Les succès et les autres événements ne comptent pas.

Les références ne sont disponibles que si `BOUKOULOU_LOGIN_AUDIT_KEY` est configurée. Aucun mot de passe, JWT, identifiant ou adresse IP en clair n'est ajouté aux alertes. La mémoire est bornée et protégée par un verrou.

**Limites** : compteur en mémoire **par processus**, sans garantie de livraison durable, sans notification externe et sans agrégation interserveurs. En production, collecter les événements dans un SIEM ou système d'alertes centralisé avec déduplication et règles globales. Ce module n'ajoute aucun blocage, migration, connexion Redis ou action externe.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q` depuis le dossier du projet.

# Étape 93 — Notification des échecs de purge

La purge planifiée envoie **facultativement** un courriel lorsqu'une erreur survient pendant la purge ou son enregistrement d'historique. La notification n'est **jamais** activée par défaut. Elle ne contient qu'un code d'erreur technique autorisé, sans texte d'exception, IP, identité ou secret.

## Configuration (environnement du planificateur)

- `BOUKOULOU_PURGE_FAILURE_NOTIFY=enabled` : activation explicite
- `BOUKOULOU_PURGE_SMTP_HOST` : serveur SMTP accessible et de confiance
- `BOUKOULOU_PURGE_SMTP_PORT=465` : port SMTP TLS implicite
- `BOUKOULOU_PURGE_SMTP_FROM` : adresse expéditrice
- `BOUKOULOU_PURGE_SMTP_TO` : une adresse destinataire
- `BOUKOULOU_PURGE_SMTP_USER` et `BOUKOULOU_PURGE_SMTP_PASSWORD` : optionnels mais requis ensemble; secret à injecter via gestionnaire de secrets

La connexion utilise SMTP_SSL avec vérification TLS et délai de 10 secondes. L'envoi est synchrone et au mieux : une panne SMTP ne masque pas l'erreur initiale. Une erreur avant l'acquisition du verrou (ex. configuration de purge refusée) reste à signaler par le planificateur externe. Les échecs SMTP ne sont pas enregistrés dans la base d'historique; surveiller aussi le code retour et les journaux de l'ordonnanceur.

## Sécurité et limites

- Aucun SMTP contacté sans activation explicite.
- Aucune migration ou planification installée automatiquement.
- Aucune purge de données réelles effectuée.
- Configurer un SMTP de confiance et restreindre les variables d'environnement.
- Prévoir une alerte sur code retour non nul côté cron/systemd, en complément.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

# Étape 91 — Automatisation sécurisée de la purge des alertes

- Aucune tâche n'est lancée par l'API : un ordonnanceur externe (cron / timer systemd) doit appeler explicitement la commande.
- **Désactivé par défaut** : exige `BOUKOULOU_SECURITY_ALERT_STORAGE=database` et `BOUKOULOU_SECURITY_ALERT_AUTO_PURGE=enabled`.
- Nécessite PostgreSQL et la migration SQL de l'étape 89 ; aucun autre moteur accepté pour l'exécution planifiée.
- Un verrou consultatif PostgreSQL empêche deux exécutions planifiées simultanées utilisant cette commande. En cas de verrou occupé, aucun effacement n'a lieu.
- Simulation : `python -m scripts.purge_security_alerts_step91`.
- Purge effective : `python -m scripts.purge_security_alerts_step91 --apply --batch-size 500`.
- Au maximum 1000 lignes supprimées par lancement ; une seule passe, sans boucle illimitée.
- La durée de conservation reste définie par `BOUKOULOU_SECURITY_ALERT_RETENTION_DAYS` (90 jours par défaut).
- Exemple cron (à installer **manuellement** et seulement après validation) : `0 3 * * * cd /chemin/projet && /chemin/python -m scripts.purge_security_alerts_step91 --apply >> /chemin/logs/purge-alertes.log 2>&1`.
- Attention : ne jamais enregistrer d'identifiants ou de secrets dans les logs ; restreindre l'accès aux journaux et utiliser un compte SQL à privilèges minimaux.
- Faire une sauvegarde et vérifier la politique légale de conservation avant activation. Le verrou protège cette commande, pas les suppressions réalisées par d'autres outils.
- Aucun cron, déploiement, migration ni effacement sur base réelle n'a été effectué.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

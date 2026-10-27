# Étape 89 — Persistance SQL optionnelle des alertes

- Mode par défaut : **mémoire locale**, identique à l'étape 88.
- Mode opt-in : `BOUKOULOU_SECURITY_ALERT_STORAGE=database` pour enregistrer et consulter les alertes dans la base SQL configurée par `DATABASE_URL`, y compris après redémarrage et entre workers.
- Appliquer **manuellement**, après sauvegarde, `migrations/security_login_alerts_step89_DRAFT_NOT_APPLIED.sql` (PostgreSQL). Aucune migration ni création de table automatique.
- Route `GET /admin/security/login-alerts` : mêmes filtres, pagination et contrôle ADMIN, avec `scope=database` et `persistent=true` en mode SQL.
- Ne stocker que les références pseudonymisées ; protéger la clé de pseudonymisation, l'accès SQL et les sauvegardes. Définir une durée de conservation et une purge conforme aux obligations applicables.
- Si la base est indisponible lors de l'émission d'une alerte, l'échec est journalisé sans empêcher la connexion. Les alertes ne sont **pas** garanties en cas de panne ; envisager une file durable pour la production.
- Aucun déploiement, migration, ni connexion à une base réelle n'a été effectué.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

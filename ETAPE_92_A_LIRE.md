# Étape 92 — Historique des exécutions de purge

## Ajouts
- Table `security_alert_purge_runs` : date UTC, statut (`completed`, `skipped_locked`, `failed`), simulation, nombres éligibles et supprimés, taille de lot, code d'erreur technique.
- La commande planifiée de l'étape 91 écrit un bilan après une exécution réussie, ignorée (verrou occupé), ou échouée durant la purge.
- Route **GET /admin/security/purge-runs** réservée au rôle ADMIN, avec `limit` (1–200, défaut 50) et `before_id` pour pagination décroissante.
- Aucune IP, aucun identifiant utilisateur, mot de passe, jeton ou texte brut d'exception dans l'historique.

## Activation
1. Sauvegarder la base PostgreSQL.
2. Examiner puis appliquer **manuellement** `migrations/security_alert_purge_runs_step92_DRAFT_NOT_APPLIED.sql` sur la base prévue.
3. Activer le stockage et l'automatisation selon les consignes des étapes 89–91.
4. Utiliser la commande `python -m scripts.purge_security_alerts_step91` (simulation par défaut), ou `--apply` après validation.
5. Consulter `GET /admin/security/purge-runs` avec un JWT ADMIN valide.

## Limites
- La route requiert la table SQL de l'étape 92 ; sans migration, la consultation échoue (pas de création automatique).
- Si la base ou la table d'historique est indisponible, la journalisation peut échouer : une exécution `--apply` doit être réservée à un environnement vérifié et supervisé. Un échec de journalisation après une purge ne rétablit pas les suppressions déjà validées.
- Les erreurs avant acquisition du verrou (configuration invalide, connexion refusée) ne sont pas historisées en base. Le processus renvoie un code d'échec ; l'ordonnanceur doit conserver ses propres journaux et alertes.
- L'historique lui-même n'est pas encore soumis à une politique de purge.
- Aucune migration, installation cron, connexion à une base réelle ou suppression n'a été effectuée.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

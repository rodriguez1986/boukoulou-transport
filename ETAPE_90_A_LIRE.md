# Étape 90 — Politique de conservation et purge contrôlée

- Durée de conservation SQL configurable : `BOUKOULOU_SECURITY_ALERT_RETENTION_DAYS` (défaut **90 jours**, valeur autorisée 1 à 3650 jours).
- Purge **manuelle uniquement**, jamais lancée automatiquement par le serveur. La conservation s'applique uniquement aux alertes SQL de l'étape 89, pas aux journaux externes ni aux sauvegardes.
- Sauvegarder la base et vérifier la conformité légale avant la première purge.
- Pré-requis : migration de l'étape 89 appliquée et `BOUKOULOU_SECURITY_ALERT_STORAGE=database`.
- Simulation sans suppression : `python -m scripts.purge_security_alerts_step90`.
- Supprimer au plus 500 lignes par exécution : `python -m scripts.purge_security_alerts_step90 --apply`.
- Option `--batch-size 1000` (maximum 1000). Relancer en lots si nécessaire. Le bilan JSON contient la date limite, le nombre éligible et le nombre supprimé.
- Une alerte datée **exactement** à la limite n'est pas supprimée (comparaison stricte `<`).
- La suppression est irréversible dans la base active, mais les sauvegardes conservent leurs copies jusqu'à expiration de leur propre politique.
- Aucun déploiement ni aucune suppression de données réelles n'a été effectué.

Tests : `PYTHONPATH=test_support_step53:. python -m pytest -q`.

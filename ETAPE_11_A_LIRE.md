# Étape 11 — Conflits d’ouverture de caisse

La route `POST /cash/sessions/open` intercepte désormais les erreurs d’intégrité
lors de `db.commit()`, annule la transaction, et renvoie HTTP 409 avec
`CASH_ALREADY_OPEN` **uniquement** lorsque PostgreSQL indique la contrainte
`ux_cash_sessions_one_open_per_user`. Les autres erreurs d’intégrité restent
visibles au gestionnaire d’erreurs, plutôt que d’être masquées.

**Condition indispensable :** appliquer, après vérification et sauvegarde,
la migration de l’étape 10 sur la base cible. Sans cet index unique, la
protection contre deux ouvertures concurrentes n’est pas garantie.

Des tests statiques sont inclus. Aucun test de concurrence réel n’a été
réalisé sur PostgreSQL, aucune migration n’a été exécutée et aucun Docker
n’a été démarré. Ne pas utiliser en production sans tests d’intégration.

# Étape 24 — Protection des clôtures simultanées

## Modification
Dans `app/main.py`, la route `POST /cash/sessions/{session_id}/close`
charge la caisse avec `with_for_update()` avant de contrôler son état.
Sur PostgreSQL, ce verrou de ligne est maintenu jusqu'au commit/rollback.
Une seconde demande concurrente attend, relit la caisse clôturée et reçoit 409.
L'audit et la clôture restent dans la même transaction (étape 22).

## Vérifications locales
`python -m pytest -q test_cash_close_step24.py`

## Limites importantes
- Les tests de cette étape sont **statiques** : la protection concurrente doit
  être vérifiée avec deux connexions sur une **base PostgreSQL de test**.
- SQLite ne reproduit pas le comportement `SELECT ... FOR UPDATE` de PostgreSQL.
- Les sommes sont calculées après acquisition du verrou de caisse ; la
  cohérence avec des ventes ajoutées simultanément nécessitera une analyse
  supplémentaire de la logique d'encaissement.
- Aucune migration, aucun Docker et aucune base réelle ne sont lancés ici.
- Conserver l'archive précédente avant de remplacer les fichiers.

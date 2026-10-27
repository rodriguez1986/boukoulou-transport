# Étape 31 — Registre des remboursements (préparation sûre)

Cette archive complète l'étape 30 par un **diagnostic de réservation** des montants.
Les demandes `PENDING`, `PROCESSING` et `CONFIRMED` occupent le plafond ; les
`FAILED` et `CANCELLED` n'occupent pas le plafond. Une clé d'idempotence déjà
présente pour le même paiement est signalée.

## Fichiers ajoutés

- `app/refund_register_step31.py` : simulation pure sans écriture ni paiement.
- `test_refund_register_step31.py` : tests unitaires de cette simulation.
- `migrations/v59_refund_register_step31_DRAFT_NOT_APPLIED.sql` : **brouillon**
  PostgreSQL avec clé unique `(payment_id, idempotency_key)`. **Ne pas exécuter.**

## Limites impératives

La contrainte unique empêche deux demandes avec la même clé, **pas** deux
clés différentes dépassant ensemble le plafond. Le futur endpoint devra
verrouiller le paiement `FOR UPDATE`, vérifier les demandes en attente et
confirmées, et enregistrer atomiquement une réservation. Les droits ADMIN
sont provisoires ; devise, unité monétaire, remboursement partiel et PSP
restent à valider. Aucun endpoint, audit durable ou remboursement n'est créé.

## Tests

`python -m pytest -q test_refund_rules_step30.py test_refund_register_step31.py`

Aucune migration exécutée ; aucune base PostgreSQL modifiée.

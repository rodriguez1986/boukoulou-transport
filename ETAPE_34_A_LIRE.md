# Étape 34 — Registre durable des événements PSP (préparation)

## Reconstitution
Conservation intégrale du projet issu de l’étape 33; aucune fonctionnalité historique retirée.

## Amélioration
- `app/refund_event_ledger_step34.py` : prévalidation sans effet de bord, avec vérification de la référence de remboursement, montant entier positif, devise ISO alphabétique majuscule.
- `migrations/v59_refund_events_step34_DRAFT_NOT_APPLIED.sql` : **brouillon non appliqué** de table PostgreSQL, clé UNIQUE `(provider, provider_event_id)` et lien au registre de l’étape 31.
- `test_refund_event_ledger_step34.py` : tests de doublons, conflits et validations.

## Limites de sécurité
Le code ne persiste aucun événement, ne valide aucune signature PSP, n’applique aucune transition financière et ne modifie aucune base. La migration 31 et celle-ci sont des brouillons, **ne pas les exécuter en production**. Une vraie ingestion doit vérifier les signatures sur les octets bruts, garantir l’atomicité, vérifier les montants/devises et gérer les courses concurrentes.

## Tests
`python -m pytest -q test_refund_events_step33.py test_refund_event_ledger_step34.py`

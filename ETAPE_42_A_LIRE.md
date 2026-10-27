# Étape 42 — Écriture transactionnelle PostgreSQL (préparatoire)

## Reconstitution
Tous les fichiers et fonctionnalités des étapes précédentes sont conservés.

## Amélioration
- `app/payment_audit_transaction_step42.py` : fonctions DB-API pour créer un flux et son premier événement en une transaction ; verrouillage `SELECT ... FOR UPDATE` avant d'enregistrer une transition ; contrôle du dernier état, de la séquence et de l'empreinte ; `commit`/`rollback`.
- `test_payment_audit_transaction_step42.py` : tests unitaires avec **fausse connexion SQL** (pas de serveur PostgreSQL).
- Les requêtes utilisent des paramètres `%s`, pas d'interpolation de données.

## Prérequis et limites
La migration `migrations/v59_payment_audit_step41_DRAFT_NOT_APPLIED.sql` reste un **brouillon non appliqué**. Ne pas l'exécuter en production sans revue du schéma réel et tests sur une base isolée. Le code requiert une connexion PostgreSQL transactionnelle `autocommit=False`, fournie par une couche applicative future ; il n'ouvre aucune connexion lui-même. Les tests ne prouvent pas encore le comportement sous concurrence réelle.

Il reste à implémenter : authentification et autorisations de l'acteur, contrôle des signatures PSP réelles, référence aux vrais billets, isolation de la transaction et reprise des erreurs, idempotence globale, intégration FastAPI, migration approuvée, tests d'intégration PostgreSQL et contrôle d'accès aux tables. Aucun encaissement, remboursement ni émission de billet réels.

## Tests ciblés
`python -m pytest -q test_payment_audit_transaction_step42.py test_payment_audit_storage_step41.py test_payment_audit_step40.py test_payment_lifecycle_step39.py test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

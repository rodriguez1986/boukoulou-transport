# Étape 41 — Préparation de la persistance du journal d'audit

**Reconstitution :** l'ensemble de l'étape 40 est conservé.

**Amélioration :**
- `migrations/v59_payment_audit_step41_DRAFT_NOT_APPLIED.sql` propose deux tables PostgreSQL autonomes : flux de paiement et lignes d'audit, avec clés, contraintes métier et unicité de séquence.
- `app/payment_audit_storage_step41.py` prépare des données candidates à l'insertion et vérifie la cohérence du journal existant, sans écriture.
- `test_payment_audit_storage_step41.py` teste la préparation et les rejets.

**ATTENTION :** la migration est un brouillon NON APPLIQUÉ. Elle n'est pas
validée contre le schéma PostgreSQL réel et n'établit pas de lien FK avec
les billets existants. La transaction applicative, la gestion de concurrence
(`SELECT FOR UPDATE`), les permissions SQL, l'identité d'acteur authentifiée,
la protection des données et l'idempotence restent à implémenter et tester.
Aucun webhook ni paiement réel, aucun billet émis. Les empreintes SHA-256
ne protègent pas contre une personne qui peut recalculer les empreintes.

**Tests ciblés :**
`python -m pytest -q test_payment_audit_storage_step41.py test_payment_audit_step40.py test_payment_lifecycle_step39.py test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

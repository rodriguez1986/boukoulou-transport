# Étape 43 — Tests d'intégration PostgreSQL (opt-in)

**Reconstitution :** code et tests des étapes 1–42 conservés.

**Amélioration :** tests d'intégration de la couche transactionnelle étape 42,
sur un **véritable PostgreSQL de test uniquement**, avec :
- insertion initiale + transition atomiques ;
- rejet d'une référence de billet en double ;
- deux transactions concurrentes sur le même paiement : une seule réussit ;
- vérification des lignes d'audit enregistrées.

## Sécurité : aucun lancement automatique sur une base réelle

Par défaut, les tests PostgreSQL sont **ignorés** (skipped) et aucune
connexion réseau ou migration n'est effectuée. Les tests utilisent `psycopg2`
(fournir `psycopg2-binary` dans l'environnement de test si nécessaire).
Ils nécessitent une base dédiée dont le nom commence par `bt_test_` ou finit
par `_test`, et des droits `CREATE SCHEMA`. Un schéma au nom aléatoire est
créé, la migration brouillon de l'étape 41 y est appliquée, puis **seul ce
schéma de test** est supprimé après les tests.

Sur un environnement de test isolé uniquement :

```bash
python -m pip install pytest psycopg2-binary
export BT_STEP43_PG_TEST_DSN='postgresql://utilisateur:motdepasse@localhost:5432/bt_test_payments'
export BT_STEP43_PG_TEST_ENABLE=I_UNDERSTAND_TEST_DATABASE_ONLY
python -m pytest -q test_postgresql_integration_step43.py
```

Sous Windows PowerShell, définir les deux variables via `$env:...`.

**Attention :** tests PostgreSQL non exécutés lors de la construction
de cette archive en l'absence d'une base de test autorisée. Ils sont
fournis prêts à lancer, mais leur réussite réelle reste à confirmer.

Les tests ne créent aucun paiement PSP réel, ne marquent aucun billet payé
dans l'application métier et n'activent aucune API Airtel, MTN ou Moov.
Le modèle doit encore être adapté au schéma réel, aux rôles et aux droits
avant toute mise en production.

## Tests sans base
`python -m pytest -q test_postgresql_guard_step43.py test_payment_audit_transaction_step42.py test_payment_audit_storage_step41.py test_payment_audit_step40.py test_payment_lifecycle_step39.py test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

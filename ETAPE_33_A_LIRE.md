# Étape 33 — Traçabilité préparatoire des événements de remboursement

Ajout d’un diagnostic **sans effet de bord** : `app/refund_events_step33.py`.

- Détecte la répétition d’un événement par couple `(provider, event_id)`.
- Distingue une répétition identique d’un événement dont les données sont contradictoires.
- Refuse les identifiants absents, états non prévus et historiques malformés.
- Ne stocke aucune donnée, ne modifie aucun état, n’effectue aucun remboursement, ne crée aucun audit.

**Limites :** une empreinte locale n’est pas une preuve d’authenticité. Les signatures PSP, les événements authentifiés, l’unicité durable en PostgreSQL, les transactions atomiques et la protection contre les courses concurrentes restent à concevoir et à tester. Ne pas activer une API de remboursement en production sur la base de cette simulation. La migration de l’étape 31 reste un brouillon à ne pas exécuter.

## Vérification

`python -m pytest -q test_refund_rules_step30.py test_refund_register_step31.py test_refund_transitions_step32.py test_refund_events_step33.py`

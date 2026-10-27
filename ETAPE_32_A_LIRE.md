# Étape 32 — États et transitions des remboursements

Cette étape complète la simulation de registre de l'étape 31 par un **validateur pur** des transitions. Aucune API de remboursement n'est activée.

## Transitions proposées (à valider métier)

- `PENDING` → `PROCESSING` ou `CANCELLED`.
- `PROCESSING` → `CONFIRMED` ou `FAILED`.
- `CONFIRMED`, `FAILED`, `CANCELLED` : états terminaux, sans transition autorisée.
- Une confirmation exige une référence PSP ; un échec ou une annulation exige un motif.
- Le rôle `ADMIN` est provisoire et devra être confirmé.

## Nouveaux fichiers

- `app/refund_transitions_step32.py` : validation sans écriture.
- `test_refund_transitions_step32.py` : tests des transitions et refus.

## Limites de sécurité

Une référence PSP fournie par un appelant **n'est pas une preuve de remboursement**. Une future intégration devra vérifier la confirmation auprès du prestataire de paiement, authentifier les événements, gérer les répétitions et garantir l'atomicité de l'audit et des écritures. Le brouillon SQL de l'étape 31 ne doit pas être exécuté. Aucun montant, registre, paiement ou base PostgreSQL n'est modifié.

## Vérification

`python -m pytest -q test_refund_rules_step30.py test_refund_register_step31.py test_refund_transitions_step32.py`

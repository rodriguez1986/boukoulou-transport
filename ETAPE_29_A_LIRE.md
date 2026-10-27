# Étape 29 — Diagnostic des annulations et remboursements

## Constat sur le code récupéré

- `PUT /trips/{trip_id}/cancel` annule une course, mais ne rembourse pas les paiements.
- `PaymentStatus` contient `PENDING`, `SUCCESS`, `FAILED`, sans état de remboursement.
- Aucun registre de remboursements fiable n'a été identifié dans les modèles inspectés.

## Ajouts sans modification des endpoints

- `app/annulations_step29.py` : fonction `diagnostic_annulations(courses, billets, paiements, remboursements=())` en mémoire.
- `test_annulations_step29.py` : huit contrôles isolés.

Le rapport identifie les paiements `SUCCESS` liés à une course `CANCELLED`, mais ne présume **jamais** qu'un remboursement a été réalisé. Les remboursements transmis en option sont des éléments de diagnostic non certifiés. Aucun montant n'est soustrait automatiquement.

## Tests

```powershell
py -3 -m pytest -q test_annulations_step29.py
```

## Limites

Aucune API de remboursement, aucun schéma ou migration, aucune écriture PostgreSQL. Avant de créer un remboursement réel, il faut définir les droits, le lien au paiement, le montant maximal remboursable, l'idempotence, les écritures de caisse et l'audit. Les tests ne remplacent pas une validation métier et PostgreSQL.

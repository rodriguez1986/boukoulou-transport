# Étape 30 — Prévalidation des demandes de remboursement

Cette étape **n'implémente pas** de remboursement réel. Elle ajoute `app/refund_rules_step30.py`, un module Python pur pour vérifier une demande *avant* une future API.

Contrôles : rôle autorisé (ADMIN **provisoire**, à confirmer), paiement SUCCESS, montant entier strictement positif, clé d'idempotence non vide et non réutilisée pour le même paiement, plafond cumulatif des remboursements confirmés, historique incohérent.

## Limites critiques

- Le contrôle en mémoire ne prévient **pas** deux remboursements concurrents. Le futur endpoint devra verrouiller le paiement, réserver les demandes en attente et poser des contraintes uniques PostgreSQL.
- Une clé d'idempotence réutilisée est signalée ; une API future devra retourner le résultat de la demande initiale plutôt que débiter deux fois.
- Aucun registre fiable n'existe encore ; les listes de remboursements sont des données de simulation. Aucun droit métier définitif n'a été validé.
- Aucun audit réel n'est écrit ; aucune intégration PSP, caisse, base ou endpoint n'est ajoutée.
- Les montants sont supposés en unités entières de la devise de paiement ; la devise et les remboursements partiels sont à confirmer.

## Tests

`python -m pytest -q test_refund_rules_step30.py`

Aucune migration ni base de production ne doit être exécutée à cette étape.

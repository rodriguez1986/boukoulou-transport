# Étape 27 — Traçabilité guichet / bord / paiements historiques

## Constat vérifié dans le code

- `Pass59` représente un titre V5.9, qu'il ait été vendu au guichet ou à bord.
- `OnboardSale59.pass_id` référence `Pass59.id` ; une contrainte d'unicité limite à une vente à bord par titre.
- Une vente à bord est donc **également présente dans Pass59** : il ne faut pas additionner `Pass59.total` et `OnboardSale59.total_amount` sans exclusion.
- `Payment.reference` et `Pass59.reference` ne sont pas liés par une clé étrangère. Une référence commune est une **alerte**, pas une preuve de double comptage.
- `app/payment_breakdown.py` additionne actuellement les paiements historiques validés et tous les passes V5.9. Cette étape **ne change pas** ce calcul, faute de règles métier validées.

## Ajouts

- `app/traceability_step27.py` : rapprochement **en mémoire**, en lecture seule, par `pass_id`, détection des ventes à bord orphelines, doubles, écarts de montants et de caisses, et références communes avec paiements historiques.
- `test_traceability_step27.py` : dix tests isolés.

Exécuter à la racine du dossier extrait :

```powershell
py -3 -m pytest -q test_traceability_step27.py
```

## Limites

Ce diagnostic n'est pas encore branché à un endpoint et n'interroge aucune base de données. Les tests n'établissent pas la cohérence d'un jeu de données réel ni le comportement concurrent de PostgreSQL. Ne pas utiliser les alertes pour supprimer ou corriger automatiquement des recettes.

**Aucune migration et aucune modification de base de production.**

# Étape 26 — Diagnostic de risque de double comptage

Le code actuel `app/payment_breakdown.py` additionne les paiements historiques
validés (`Payment`) et les ventes V5.9 (`Pass59`). Sans lien métier prouvé entre
les deux sources, une même vente enregistrée dans les deux tables pourrait
être comptabilisée deux fois.

## Ajouts

- `app/reconciliation_step26.py` : détecte les **références identiques** présentes
  dans les deux ensembles de données, sans modifier les calculs financiers.
- `test_reconciliation_step26.py` : six tests sur les cas d'alerte, de statut et
  sur le code existant.

## Exécution (à la racine du dossier extrait)

```powershell
py -3 -m pytest -q test_reconciliation_step26.py
```

## Prudence

Une référence identique constitue un **signal de rapprochement**, pas une
preuve définitive de doublon. Des références différentes n'excluent pas non
plus un doublon. Aucun dédoublonnage automatique n'est appliqué aux recettes.
Le rapprochement devra être validé avec les règles métier, la structure des
ventes à bord et des données réelles **anonymisées** dans une base de test.

Aucune migration, connexion PostgreSQL ou opération de production n'est requise.

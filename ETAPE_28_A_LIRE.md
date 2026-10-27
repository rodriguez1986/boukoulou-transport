# Étape 28 — Rapprochement conservateur des recettes

## Objectif

Ajouter un rapport **en mémoire, sans écriture** pour distinguer les paiements historiques validés, les passes V5.9 et les ventes à bord. Une vente à bord étant déjà représentée dans les passes, elle n'est pas ajoutée une seconde fois.

## Ajouts

- `app/reconciliation_step28.py` : `rapport_rapprochement(paiements, passes, ventes_bord)`.
- `test_reconciliation_step28.py` : six tests isolés.

Les références communes sont signalées **A_VERIFIER**, même si le montant et la caisse correspondent. Le total brut affiché n'est **pas un total certifié sans doublon**. Aucune suppression ou déduction automatique. Le calcul utilisé par les endpoints existants reste inchangé.

## Vérification

```powershell
py -3 -m pytest -q test_reconciliation_step28.py test_traceability_step27.py
```

## Limites

Pas d'endpoint ajouté, pas de connexion à une base réelle, pas de test de concurrence PostgreSQL. Le rapport ne prouve pas que deux lignes correspondent à une même transaction. Avant toute déduplication, il faudra définir et valider les règles métier, les identifiants canoniques et les cas de remboursements.

**Aucune migration ni modification de la base de production.**

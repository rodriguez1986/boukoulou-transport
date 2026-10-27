# Étape 25 — Cohérence des recettes et clôture de caisse

Cette étape ajoute `test_cash_reconciliation_step25.py`.

Les tests vérifient :
- que consultation et clôture utilisent la même fonction de ventilation des recettes ;
- que le fonds initial s'ajoute uniquement aux encaissements `CASH` ;
- que l'écart = montant déclaré − montant attendu ;
- que le total commercial correspond à la somme des moyens de paiement ;
- que les paiements historiques ne sont comptés qu'au statut `SUCCESS` ;
- que la ventilation des recettes fonctionne sur des résultats SQL **simulés** ;
- que les garde-fous transactionnels des étapes 22 et 24 restent présents.

## Lancer les tests

Après extraction, dans le dossier racine du projet :

```powershell
py -3 -m pytest -q test_cash_reconciliation_step25.py
```

En cas de dépendances manquantes, utiliser le script de l'étape 14 pour préparer
un environnement virtuel, puis relancer cette commande dans celui-ci.

## Limites et points à vérifier ensuite

Les données de ventes utilisées dans le test fonctionnel sont simulées.
Aucune connexion PostgreSQL n'est effectuée. Il reste à vérifier en base de test
l'absence de double comptage entre `Payment` et `Pass59`, en particulier pour
les ventes à bord, ainsi que la cohérence lors d'encaissements simultanés à une
clôture. La protection de la seule ligne `CashSession` ne verrouille pas
nécessairement les insertions de ventes concurrentes.

Ne pas utiliser cette archive comme preuve de validation en production.

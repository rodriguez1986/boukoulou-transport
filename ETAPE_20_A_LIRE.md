# Étape 20 — Audit des permissions des caisses

Cette archive conserve l'étape 19 et ajoute `test_cash_permissions_step20.py`.
Les cinq tests analysent **le code des routes réelles** de `app/main.py` :
- ouverture et consultation : ADMIN, AGENT, CONTROLLER ;
- clôture : mêmes rôles, avec contrôle de propriété (exception ADMIN) ;
- rectification : ADMIN uniquement, avec verrouillage et caisse clôturée ;
- historique, tableau de bord et exports : ADMIN uniquement ;
- DRIVER : exclu des routes de caisse vérifiées.

## Commande locale
Depuis le dossier extrait :

```powershell
py -3 -m pytest -q test_cash_permissions_step20.py
```

**Important :** ces contrôles sont statiques. Ils confirment les règles écrites
mais **ne démontrent pas** que toutes les réponses HTTP 401/403 sont correctes.
Ils n'effectuent aucune écriture en base. Les scénarios HTTP isolés de l'étape 19
restent à exécuter dans un environnement disposant des dépendances.

## Point fonctionnel à confirmer
Le rôle CONTROLLER peut ouvrir et clôturer **sa propre caisse** selon les règles
actuelles. Si le métier exige une consultation seule pour les contrôleurs,
une décision explicite et une modification du backend seront nécessaires.

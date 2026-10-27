# Étape 21 — Vérification de la clôture de caisse

Cette étape conserve les fichiers de l'étape 20 et ajoute
`test_cash_close_step21.py` avec six tests **statiques** (lecture du code),
qui contrôlent les autorisations, les états, les calculs de caisse,
la clôture, l'audit et les rectifications.

## Exécution locale

Depuis le dossier extrait :

```powershell
py -3 -m pytest -q test_cash_close_step21.py
```

Si pytest n'est pas installé, utiliser l'environnement de test créé
aux étapes précédentes.

## Points d'attention

- Le montant attendu de la caisse physique est le fonds initial +
  les encaissements **CASH** ; les paiements électroniques restent
  dans les recettes commerciales mais pas dans le tiroir-caisse.
- Le rôle CONTROLLER a toujours la permission de clôturer sa caisse.
- Les six tests ne prouvent **pas** le bon fonctionnement réel de la
  comptabilité ni l'absence de double comptage dans les données.
- Le code existant enregistre la clôture (`db.commit`) avant de
  déclencher `audit(...)`. Il faut vérifier à une prochaine étape
  l'atomicité de la clôture et de son audit, notamment si l'audit échoue.
- Aucun serveur, Docker, PostgreSQL ou migration n'est lancé.

# Étape 22 — Atomicité de la clôture et de l'audit

## Correction apportée

Dans `app/main.py`, la route `POST /cash/sessions/{session_id}/close`
ajoute désormais l'enregistrement `Audit(CLOSE_CASH_SESSION)` à la même
transaction SQLAlchemy que le changement d'état de la caisse. Un seul
`db.commit()` valide les deux. Si la validation échoue, `db.rollback()`
annule les changements en base et l'erreur est propagée.

Avant cette correction, l'audit était appelé **après** le commit de clôture,
ce qui permettait une caisse clôturée sans audit si la seconde opération échouait.

## Vérification locale

Depuis le dossier extrait :

```powershell
py -3 -m pytest -q test_cash_atomicity_step22.py
```

Ces cinq tests sont **statiques** : ils vérifient la structure du code et
non une transaction réelle sur PostgreSQL. Des tests d'intégration sur
base de test restent indispensables (échec simulé d'insertion Audit,
rollback, concurrence et droits d'accès).

## Précautions

- Aucune migration, connexion à PostgreSQL ni démarrage Docker n'a été réalisé.
- Ne pas déployer sans sauvegarde et validation des tests d'intégration.
- Le rôle CONTROLLER conserve les droits de clôture définis auparavant.
- La fonction d'audit commune aux autres routes n'a pas été modifiée :
  cette correction concerne uniquement la clôture de caisse.

- Le test historique `test_commit_et_audit` de l’étape 21 a été adapté
  à la nouvelle transaction atomique, sans changer ses autres contrôles.

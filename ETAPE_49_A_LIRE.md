# Étape 49 — Administration sécurisée des affectations de bord

## Reconstitution
Tous les fichiers des étapes 1 à 48 sont conservés, sans modification des routes de production.

## Amélioration
Nouveau service `app/crew_assignment_admin_step49.py` :
- `attribuer(db, actor_id, target_user_id, trip_id, starts_at, ends_at=None)` :
  crée une affectation `DRIVER` ou `CONTROLLER`, et une ligne d'audit.
- `retirer(db, actor_id, assignment_id)` : désactive et journalise.
- `consulter(db, actor_id, trip_id)` : liste les affectations du voyage.

L'identité de l'administrateur doit venir du JWT validé côté serveur.
Seuls `ADMIN` (global) et `COUNTRY_MANAGER` (dans son pays) peuvent administrer.
Le compte cible doit être actif, de rôle DRIVER/CONTROLLER et du pays du voyage.
Les doublons actifs chevauchants sont refusés. Création/révocation et audit
partagent une transaction SQLAlchemy avec commit/rollback.

## Limites
- Service non connecté aux routes de production ; aucun paiement ou embarquement.
- La migration PostgreSQL est un **brouillon non appliqué**.
- Tests SQLite : ils ne prouvent pas le comportement concurrent PostgreSQL.
- La protection contre les créations simultanées utilise un verrou de ligne Trip
  avec PostgreSQL ; elle ne protège pas contre des écritures hors de ce service.
- Les traces DB ne sont pas inviolables sans privilèges d'écriture séparés.
- Revue de la politique ADMIN/SUPER_ADMIN, des conflits d'affectation entre
  différents voyages et des contraintes DB requise avant mise en production.

## Tests
`python -m pytest -q test_crew_assignment_admin_step49.py test_crew_assignment_step48.py`

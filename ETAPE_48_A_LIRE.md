# Étape 48 — Affectations sécurisées des chauffeurs et contrôleurs aux voyages

## Reconstitution
Tous les fichiers des étapes 1 à 47 sont conservés.

## Amélioration
- Nouveau modèle `CrewAssignmentStep48` : rattachement explicite d'un compte
  `User` à un `Trip` avec rôle `DRIVER` ou `CONTROLLER`, période de validité,
  activation et identité de l'utilisateur ayant créé l'affectation.
- `verifier_acces_voyage(db, user_id, trip_id, action)` charge l'utilisateur,
  le voyage, sa ligne, les pays et les affectations depuis la session SQLAlchemy.
  Il refuse les comptes inactifs, pays différents, rôles non autorisés,
  affectations absentes, expirées ou non encore commencées.
- Les chauffeurs et contrôleurs ont les mêmes autorisations **de principe**
  pour consulter les passagers et le voyage, contrôler un billet et autoriser
  une validation d'embarquement. Les encaissements espèces restent régis par
  les étapes 44 à 47.
- Migration SQL **brouillon, non appliquée** dans `migrations/`.

## Limites et sécurité
Ce module **n'est pas branché aux routes de production**. Aucun paiement,
aucun contrôle QR ni embarquement réel n'est effectué. Le résultat est une
prévisualisation : toute action ultérieure doit revérifier les droits dans
sa propre transaction. Aucune interface d'attribution d'affectation n'est
encore fournie. Le champ `assigned_by_user_id` enregistre une référence,
mais n'implique pas à lui seul une autorisation administrative.

Le schéma historique `Driver`/`Trip.driver_id` ne lie pas de façon fiable
un compte `User` au chauffeur : il n'est pas utilisé comme preuve d'accès.
Avant production, vérifier la stratégie d'affectation, les conflits horaires,
les rôles exacts et le déploiement de la migration par un DBA.

## Tests
`python -m pytest -q test_crew_assignment_step48.py`

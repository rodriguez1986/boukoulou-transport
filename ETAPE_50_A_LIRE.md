# Étape 50 — Routes FastAPI de gestion des affectations (non activées)

## Reconstitution
Conserve les étapes précédentes, dont le service transactionnel étape 49.

## Amélioration
`app/crew_assignment_api_step50.py` expose un routeur **non monté** :
- `POST /api/step50/crew-assignments` : attribuer un membre d'équipage ;
- `POST /api/step50/crew-assignments/retirer` : retirer une affectation ;
- `GET /api/step50/crew-assignments/voyage/{trip_id}` : consulter.

L'acteur est tiré de `security.user`, dépendance JWT de l'application,
**jamais d'un actor_id envoyé par le client**. Le service étape 49 vérifie
ADMIN (portée globale) ou COUNTRY_MANAGER (portée pays), les comptes
DRIVER/CONTROLLER, les voyages et les périodes, et écrit l'audit dans
la même transaction. Les erreurs métier renvoient un message générique.

## Important
- Le routeur n'est **pas** branché dans `app/main.py` : pas d'accès réel.
- Les tests HTTP utilisent une identité injectée par dépendance ; ils ne
  prouvent **pas** la vérification d'une signature JWT réelle.
- Aucun schéma PostgreSQL n'est appliqué ; le brouillon de migration des
  étapes 48/49 doit être revu et testé avant tout déploiement.
- Les autorisations d'embarquement et encaissements réels restent non branchées.
- Le rôle technique `ADMIN` correspond au super administrateur historique.

## Tests
`python -m pytest -q test_crew_assignment_api_step50.py test_crew_assignment_admin_step49.py test_crew_assignment_step48.py`

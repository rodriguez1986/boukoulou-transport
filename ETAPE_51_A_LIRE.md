# Étape 51 — Vérification JWT réelle sur une base de test isolée

## Reconstitution
Toutes les étapes 1–50 sont conservées sans activation de routes.

## Amélioration
- `test_crew_assignment_jwt_step51.py` : scénarios d'intégration HTTP
  avec de **vrais JWT signés**, vérifiés par `app.security.user`, et
  une base **SQLite en mémoire** isolée : création et retrait avec audit,
  refus de rôle et de pays, JWT absent/invalide/révoqué, compte inactif,
  `actor_id` falsifié.
- `test_crew_assignment_jwt_contract_step51.py` : contrôles structurels
  qui s'exécutent même lorsque `passlib` manque.

## Exécution
Installer les dépendances de `requirements.txt` dans un environnement
de test dédié, puis :

    python -m pytest -q test_crew_assignment_jwt_step51.py test_crew_assignment_jwt_contract_step51.py

**Attention :** si `passlib` ou `PyJWT` manque, le module de tests JWT
est *ignoré*, et non considéré comme réussi. Le rapport de tests
doit distinguer les tests exécutés des tests ignorés.

## Sécurité et limites
- Le routeur de l'étape 50 reste non monté dans `app/main.py`.
- Aucune migration, écriture sur la base réelle, activation PSP,
  encaissement ou validation de billet n'est effectuée.
- Les tests sont conçus pour SQLite et ne prouvent pas la
  concurrence ni les transactions PostgreSQL en production.
- Avant activation, tester le parcours complet avec les dépendances
  et schémas de test réellement utilisés, puis valider PostgreSQL.

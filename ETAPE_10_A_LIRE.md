# Étape 10 — Contrainte d'unicité des caisses ouvertes

## Livrables
- `migrations/v59_one_open_cash_session_step10.sql` : index unique partiel PostgreSQL
  sur `cash_sessions(user_id)` lorsque `status = 'OPEN'`.
- `test_cash_integrity_step10.py` : vérifications statiques et contrôle PostgreSQL
  **optionnel, en lecture seule**, activé uniquement avec `BOUKOULOU_TEST_DATABASE_URL`.

## Précautions
La migration **n'a pas été exécutée**. Sauvegarder la base et examiner les caisses
ouvertes en double avant de l'appliquer. L'index ne remplace pas la gestion des
erreurs d'intégrité (`IntegrityError`) côté API en cas de concurrence ; ce
traitement devra être ajouté et testé dans une étape suivante.

`CREATE INDEX CONCURRENTLY` ne s'exécute pas à l'intérieur d'une transaction
explicite. Un échec peut laisser un index invalide. Ne pas lancer le script
automatiquement au démarrage de Docker.

## Validation
Les tests statiques ne prouvent ni la compatibilité du schéma existant, ni
l'absence de courses concurrentes. Aucun test d'intégration réel n'a été
effectué sur une base PostgreSQL. Ne pas déployer en production.

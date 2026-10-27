# Étape 55 — Préparation des tests de concurrence

## Reconstitution
Toutes les étapes 1 à 54 sont conservées sans activation des routes.

## Amélioration
- Tests de contrat vérifiant le verrou de voyage, le rejet des affectations chevauchantes, le rollback et l'absence d'activation des routes.
- Test PostgreSQL **facultatif** avec deux connexions et transactions distinctes, démontrant un blocage via `pg_advisory_xact_lock` et un `lock_timeout` (SQLSTATE 55P03). Ce test ne crée ni ne modifie de table.

## Exécution
```bash
python -m pytest -q test_crew_concurrency_step55.py
```
Sur une base PostgreSQL **isolée**, avec pilote `psycopg` installé :
```bash
export BT_STEP55_TEST_DATABASE_URL='postgresql+psycopg://.../base_de_test'
export BT_STEP55_CONFIRM_ISOLATED_DB=YES
python -m pytest -q test_crew_concurrency_step55.py
```

## Limites importantes
- Le test de deux sessions PostgreSQL est **ignoré** sans base isolée.
- Le verrou consultatif testé n'est pas le `FOR UPDATE` de `attribuer` : il ne démontre pas que deux administrateurs ne peuvent jamais créer de doublon dans le modèle réel.
- Le verrouillage actuel est **par voyage** ; deux voyages différents ne sont pas sérialisés pour un même utilisateur. La politique de conflits inter-voyages doit être définie avant d'en garantir l'absence.
- Pas de migration appliquée, pas de route montée, pas de paiement réel.

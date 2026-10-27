# Étape 54 — Préparation PostgreSQL avant activation

## Reconstitution
Les étapes 1–53 restent conservées, notamment les correctifs de caisse et les tests JWT.

## Amélioration
`test_crew_postgresql_step54.py` ajoute trois contrôles :
1. compilation du verrou `SELECT ... FOR UPDATE` en dialecte PostgreSQL ;
2. contrôle des deux migrations SQL **toujours à l'état de brouillons non appliqués** ;
3. essai facultatif de `FOR UPDATE` sur une table **temporaire**, dans une transaction annulée, sur une **base PostgreSQL de test dédiée**.

## Exécution
Sans serveur PostgreSQL :

    python -m pytest -q test_crew_postgresql_step54.py

Sur une base PostgreSQL de test exclusivement, après validation de son isolement :

    export BT_STEP54_TEST_DATABASE_URL='postgresql+psycopg://.../base_de_test'
    export BT_STEP54_CONFIRM_ISOLATED_DB=YES
    python -m pytest -q test_crew_postgresql_step54.py

Ne pas utiliser une base de production. Le test PostgreSQL est **ignoré** sans les variables ci-dessus ; ne pas le présenter comme validé.

## Limites et sécurité
- Ce contrôle n'est pas une preuve de concurrence multi-transactions ni de fonctionnement des migrations.
- Aucune migration SQL n'est exécutée, aucune table applicative n'est modifiée.
- Le routeur `crew_assignment_api_step50` reste non monté dans `app/main.py`.
- Validation à venir : base de test PostgreSQL, vraie dépendance `passlib`, migrations en staging et concurrence de deux sessions.

# Étape 12 — Tests de concurrence PostgreSQL (optionnels)

Le fichier `test_cash_concurrency_step12.py` prépare 4 scénarios : deux ouvertures
simultanées pour un même utilisateur, deux utilisateurs distincts, réouverture
après clôture, et indépendance entre utilisateurs.

**Sécurité :** ces tests sont ignorés par défaut. Ils exigent à la fois
`BOUKOULOU_TEST_DATABASE_URL` pointant vers une base PostgreSQL dont le nom se
termine par `_test`, et `BOUKOULOU_ALLOW_TEST_DB_WRITE=YES`. Ils créent puis
suppriment une table isolée portant un nom aléatoire. Ils ne modifient aucune
table métier `cash_sessions` et ne lancent aucune migration.

Exemple sous PowerShell, uniquement après création d'une base de test dédiée :

```powershell
$env:BOUKOULOU_TEST_DATABASE_URL = "postgresql+psycopg://UTILISATEUR:MOTDEPASSE@localhost:5432/boukoulou_test"
$env:BOUKOULOU_ALLOW_TEST_DB_WRITE = "YES"
python -m pytest -q test_cash_concurrency_step12.py
```

Ne pas utiliser de base de production, même avec le suffixe `_test`.
Le test ne valide que le comportement de la contrainte sur une table de
simulation. Il ne remplace pas un test d'intégration HTTP de l'API, ni un
test de migration sur une copie de la base. Aucun test PostgreSQL réel n'a
été exécuté dans la préparation de cette archive.

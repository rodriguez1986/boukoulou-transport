# Étape 46 — Tests d'intégration JWT et autorisations FastAPI

## Reconstitution
Les fichiers et les fonctions des étapes 1 à 45 sont conservés.

## Amélioration
- `test_payment_jwt_integration_step46.py` : 12 tests HTTP avec `FastAPI`
  `TestClient`, vrai décodage et contrôle JWT de `security.user`, et fausse
  session de base de données (aucun PostgreSQL réel).
- Cas couverts : jeton valide, absent, signature incorrecte, expiration,
  révocation par version, utilisateur inactif, rôle interdit, pays interdit,
  moyen interdit, champs manquants et sujet invalide.
- `test_payment_jwt_contract_step46.py` : 3 contrôles structurels exécutables
  sans la dépendance `passlib`.

## Installation des dépendances de test
Dans un environnement virtuel dédié et **sans déployer** :
`python -m pip install -r requirements.txt`
Puis `python -m pytest -q test_payment_jwt_integration_step46.py test_payment_jwt_contract_step46.py`

**ATTENTION :** si `passlib` manque, le module de tests JWT est
explicitement marqué « skipped ». Il ne faut pas interpréter ce statut
comme un succès des tests d'authentification.

## Limites
- Le routeur étape 45 reste **non monté** dans `app/main.py`.
- Les tests HTTP ne valident pas PostgreSQL ni un fournisseur PSP réel.
- Aucun paiement réel, aucune émission de billet, aucune migration appliquée.
- Avant activation, revoir la correspondance des rôles métier, la portée pays
  et la configuration `JWT_SECRET` de production.
- Étape suivante envisagée : validation des permissions sur une base de test
  et audit des erreurs sans divulgation d'informations sensibles.

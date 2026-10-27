# Étape 53 — Exécution des tests JWT d'affectation

## Reconstitution
L'intégralité des fichiers et fonctionnalités des étapes 1 à 52 est conservée.

## Amélioration : validation sans accès réseau
Les tests HTTP JWT de l'étape 51 sont exécutables dans cet environnement grâce à un composant de remplacement **exclusivement réservé aux tests** situé dans `test_support_step53/passlib/`. Il ne contient aucune implémentation de hachage de mots de passe : ses méthodes `hash` et `verify` lèvent explicitement une erreur. Ne jamais placer ce dossier sur le `PYTHONPATH` de production ni le déployer.

La signature et la vérification JWT sont réelles (PyJWT HS256) ; le contrôle des mots de passe avec la vraie bibliothèque `passlib` reste non testé. Une clé JWT forte de test est utilisée pour éviter les avertissements de clé faible.

## Commandes et résultats réellement observés
Depuis la racine du projet :

```bash
JWT_SECRET='step53-isolated-test-key-with-at-least-32-bytes-2026' PYTHONPATH="$PWD/test_support_step53:$PWD" python -m pytest -q test_crew_assignment_jwt_step51.py test_crew_assignment_jwt_contract_step51.py
# 15 passed

python -m pytest -q --disable-warnings
# 413 passed, 15 skipped
```

Ces deux suites se chevauchent : ne pas additionner leurs résultats.

## Reste à valider
- Installer `passlib[bcrypt]` depuis un dépôt fiable dans un environnement de test disposant du réseau et relancer les tests sans remplacement.
- Tester la connexion et la vérification de mots de passe avec la vraie dépendance.
- Tester migrations et verrouillages PostgreSQL dans un environnement isolé avant activation.
- Configurer `JWT_SECRET` robuste en production et supprimer tout recours à la valeur par défaut `dev-secret`.

Le routeur expérimental de l'étape 50 n'est toujours pas monté dans `app/main.py`. Aucune base réelle ni aucun PSP n'a été utilisé.

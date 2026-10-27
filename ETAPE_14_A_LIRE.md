# Étape 14 — Environnement isolé pour les tests HTTP FastAPI

Cette étape prépare un script Windows PowerShell :
`scripts/tester_http_etape14.ps1`.

Il crée `.venv` localement, installe les dépendances épinglées du projet
(`requirements.txt`) puis lance les tests de caisse des étapes 13 et 14.

## Sur Windows
1. Extraire **toute** l'archive dans un nouveau dossier.
2. Ouvrir PowerShell dans le dossier extrait.
3. Exécuter : `powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\tester_http_etape14.ps1`
4. Conserver et communiquer la sortie des tests en cas d'échec.

Ce script nécessite Python 3, Internet pour les dépendances et ne doit être
lancé que dans un environnement de développement. Il ne lance pas Docker,
ne crée pas de base PostgreSQL et n'exécute pas de migration.

## Ce qui a été vérifié ici
Les trois tests statiques de l'étape 14 ont été exécutés.
Les tests HTTP de l'étape 13 n'ont pas pu être exécutés dans cet environnement,
faute de toutes les dépendances. Ils devront être relancés sur Windows.
Leur présence dans l'archive ne prouve pas leur succès.

**Attention** : `test_cash_api_step13.py` simule une dépendance utilisateur et
une connexion DB ; ce n'est pas un test complet de la sécurité JWT ni de la
concurrence PostgreSQL. Ne pas déployer en production.

# Étape 17 — Test d'import FastAPI isolé

Cette étape reprend l'archive de l'étape 16 et ajoute :

- `scripts/diagnostic_import_etape17.py` : lance l'import FastAPI dans un processus séparé, avec SQLite **en mémoire**, amorçage des données désactivé et secret JWT réservé aux tests.
- `scripts/tester_import_etape17.ps1` : crée un environnement virtuel Windows, installe les dépendances et exécute le diagnostic et les tests.
- `test_import_step17.py` : quatre tests statiques des protections contre les écritures automatiques.

## Sous Windows

1. Extraire l'archive dans un nouveau dossier.
2. Ouvrir PowerShell dans ce dossier.
3. Exécuter :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\tester_import_etape17.ps1
```

4. Si une erreur apparaît, **copier la sortie complète** et la transmettre avant de poursuivre.

## Limites

L'import FastAPI n'a pas été exécuté avec toutes les dépendances dans notre environnement de préparation. Le script permet de faire cette vérification sur un poste de développement. Il ne crée pas de tables, ne lance pas de migration et ne se connecte pas à PostgreSQL. Il ne valide pas encore les appels HTTP, les modèles en conditions réelles ou le démarrage Docker. Ne pas utiliser en production.

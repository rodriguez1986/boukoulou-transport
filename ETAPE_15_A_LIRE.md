# Étape 15 — Diagnostic de démarrage et contrat HTTP

Cette archive reprend tous les fichiers de l'étape 14 et ajoute :
- `scripts/diagnostic_etape15.py` : inventaire des dépendances manquantes
  et vérification syntaxique de sept modules backend, **sans démarrer l'API**.
- `test_cash_api_step15.py` : cinq contrôles statiques des routes de caisse,
  de la réponse 409, du rollback et de la migration préparée.

## Sur Windows (PowerShell)
Après extraction complète, dans le dossier du projet :
```
py -3 scripts/diagnostic_etape15.py
py -3 -m pytest -q test_cash_api_step15.py
```
Si `pytest` manque, utiliser l'environnement virtuel préparé à l'étape 14
et y installer les dépendances. Ne pas exécuter Docker ou les migrations.

## Limites
Les tests statiques ne remplacent pas les tests HTTP avec `TestClient`.
Les tests HTTP des étapes 13 et 14 ne sont pas encore validés ici
car `passlib` est absent de l'environnement d'exécution.
Les tests de concurrence PostgreSQL sont encore à réaliser sur une
base isolée. Aucun démarrage complet du backend ni migration exécutée.

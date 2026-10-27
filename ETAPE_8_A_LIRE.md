# Étape 8 — Audit des autorisations financières

## Résultat
- `/finance/summary` et `/finance/audit/cash-anomalies` : `ADMIN` uniquement.
- Tableaux de bord et exports de caisse `/admin/...` : `ADMIN` uniquement.
- Indicateurs `/cash/daily`, `/cash/daily/details`, `/cash/by-line`, `/cash/by-trip` : `ADMIN` ou `AGENT` ; le code limite les agents à leurs propres ventes.
- Le rôle `COUNTRY_MANAGER` n'est pas autorisé sur les routes financières examinées. **Ce n'est pas une implémentation d'une vue financière nationale** : le périmètre fonctionnel doit être confirmé avant de l'ajouter.
- Les sessions de caisse ouvertes et clôturées acceptent certains rôles opérationnels ; les contrôles d'appartenance à une session et les éventuels accès inter-pays doivent encore être vérifiés par tests d'intégration.

## Contrôles
Le fichier `test_finance_permissions_step8.py` contient quatre tests statiques de non-régression.
Ces tests ne remplacent pas des tests avec PostgreSQL, des vrais jetons JWT et des utilisateurs Congo/Gabon.
Aucune migration ni base de données n'a été modifiée. Ne pas déployer en production.

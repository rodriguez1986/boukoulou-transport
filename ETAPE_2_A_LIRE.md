# Boukoulou Transport V5.9 — reconstruction étape 2

## Ajout vérifié
- Modèle SQLAlchemy `OnboardSale59` dans `app/v59.py`.
- Migration SQL indicative et **non exécutée** : `migrations/v59_onboard_sales_reconstruction.sql`.
- Champs utilisés par `main.py` : `id`, `pass_id`, `trip_id`, `controller_id`, `cash_session_id`, `total_amount`.
- Contrainte d’unicité sur `pass_id` pour éviter deux lignes de ventes à bord pour un même titre.

## Limites
Ce modèle est reconstitué depuis les références de `main.py` ; il n’est pas garanti identique au modèle original perdu. La vente à bord elle-même et les règles des frais (50 XAF + 50 XAF en cas d’impression) **ne sont pas encore rétablies ni testées**. Les modules `pdf_reports.py`, `finance_dashboard.py` et `finance_audit.py` manquent toujours ; l’application n’est pas prête à démarrer. La migration ne doit pas être exécutée sur une base existante sans sauvegarde et vérification du schéma.

## Vérification
Analyse syntaxique de tous les modules Python présents, sans exécution et sans connexion à PostgreSQL.

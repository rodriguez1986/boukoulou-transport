# Étape 3 — Reconstruction des modules financiers

Fichiers ajoutés : `app/pdf_reports.py`, `app/finance_dashboard.py`, `app/finance_audit.py`.

- PDF de clôture : reconstitution fonctionnelle à partir des données transmises par `main.py`, sans modification de la base.
- Tableau de bord : **résumé minimal** protégé ADMIN, non équivalent à l'ancien tableau de bord.
- Audit : **détection limitée** des écarts de caisses clôturées, non équivalente à un audit complet.
- `reportlab==4.2.5` ajouté aux dépendances.

Les contrôles effectués sont uniquement syntaxiques. Aucun test de connexion PostgreSQL, d'intégration, de PDF avec données réelles ou de sécurité n'a été réalisé. Ne pas déployer ni encaisser de l'argent avec cette version. Ne pas exécuter de migration sur une base existante sans sauvegarde. `main.py` fait encore référence à `CashSessionRectification` qui peut être absent des modèles : il faut poursuivre l'audit avant le lancement.

# Boukoulou Transport V5.9 — reconstruction du 24 octobre 2026

## Origine et état

Cette archive rassemble les fichiers fournis par l'utilisateur le 24 octobre, l'archive originale `boukoulou_v5_9_pilote.zip` retrouvée dans ses fichiers et le code partiellement reconstitué le 23 octobre. Les versions sources sont conservées dans `sources_originales/`.

**Il ne s'agit PAS encore d'une version prête à lancer ou à déployer.** Les fichiers Python présents dans `app/` passent une vérification de syntaxe AST, mais leur import, leur fonctionnement HTTP et leur intégration PostgreSQL n'ont pas été validés.

## Contenu

- `app/main.py`, `app/models.py`, `app/security.py` : reconstruction avec contrôles `COUNTRY_MANAGER` issus des étapes précédentes.
- `app/db.py`, `app/schemas.py`, `app/v59.py`, `app/cash_v59.py` : fichiers retrouvés.
- `ui/index.html`, `ui/js/app.js`, `ui/js/v59.js`, `ui/css/app.css` : interface retrouvée.
- `docker-compose.yml`, `Dockerfile`, `.env.example`, `requirements.txt` : configuration retrouvée, non mise à jour.
- `migrations/v59.sql` : migration historique de l'archive V5.9 pilote.
- `sources_originales/` : copies des originaux utiles, sans modification.

## Éléments manquants ou à réconcilier

1. `app/payment_breakdown.py`, `app/pdf_reports.py`, `app/finance_dashboard.py` et `app/finance_audit.py` : `main.py` les importe mais ils ne sont pas présents. **L'API ne peut pas démarrer en l'état.**
2. `app/v59.py` retrouvé est la version pilote : le code financier récent peut attendre d'autres classes (`OnboardSale59`) qui n'y figurent pas. Il faut retrouver la version plus récente ou reconstituer ces ajouts.
3. `ui/js/gps.js`, les changements GPS dans `ui/index.html`, les paramètres Docker GPS, les assets du logo et les scripts SQL ultérieurs ne sont pas disponibles dans cette archive.
4. Les tables et colonnes `cities`, `country_id` sur `users`, les changements `COUNTRY_MANAGER` et les migrations postérieures à la V5.9 pilote ne sont pas reconstitués intégralement.
5. La base de données PostgreSQL, ses données et les comptes réels ne sont pas inclus.
6. La sécurité territoriale n'est pas terminée : les endpoints anonymes et financiers demandent un audit supplémentaire. Aucun compte `COUNTRY_MANAGER` ne doit être activé avant validation.
7. Les tests de l'étape 224 n'ont pas été exécutés sur cette reconstruction.

## Précautions

- Ne pas lancer `docker compose up` sur une base contenant des données importantes.
- Ne pas lancer `docker compose down -v`, ne pas effacer les volumes PostgreSQL.
- Ne pas lancer les migrations sur une base existante sans sauvegarde valide.
- Ne pas encaisser de vrai argent avec la version pilote.
- Ne pas exposer publiquement la configuration Docker fournie : les identifiants de démonstration doivent être remplacés.

## Prochaine étape

Retrouver les modules financiers manquants, réconcilier la billetterie V5.9 récente, puis vérifier les imports, les routes et les tests dans un environnement de test isolé. La dernière étape confirmée dans nos échanges était l'étape 223 ; l'étape 224 restait à tester.

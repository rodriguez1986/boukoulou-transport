# Étape 60 — API administrative JWT pour les anomalies d’affectation

## Reconstitution
Tous les fichiers des étapes 1 à 59 sont conservés.

## Amélioration
- `app/crew_assignment_report_api_step60.py` : GET `/api/step60/crew-assignment-anomalies` avec JWT, ADMIN global, COUNTRY_MANAGER limité à son pays, refus des autres rôles.
- `app/crew_assignment_report_step59.py` : filtre SQL sur le pays du voyage AVANT la pagination et AVANT l’analyse des audits, pour éviter toute fuite inter-pays.
- Pagination `limit` (1 à 500), `after_id` (>=0). Le rapport reste en lecture seule.
- `test_crew_assignment_report_api_step60.py` : tests de filtrage, paramètres invalides et contrat d’accès.

## Précautions
- Routeur **non monté** dans `app/main.py`, donc **non activé en production**.
- Ne pas activer sans essais HTTP/JWT réels, test PostgreSQL et revue de sécurité.
- La clé JWT de développement `dev-secret` dans `app/security.py` doit être remplacée en production.
- La pagination n’offre pas un instantané global lors d’écritures concurrentes.
- Aucune migration ni paiement réel.

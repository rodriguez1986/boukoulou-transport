# Étape 7 — Restriction des accès anonymes

Les GET `/countries`, `/lines`, `/vehicles`, `/trips` exigent maintenant un JWT. Le GET `/countries` est filtré par pays pour COUNTRY_MANAGER ; les filtres existants des autres routes sont conservés.

Les pages `/`, `/static` et `/health` restent publiques intentionnellement. Les autres routes, notamment finances, GPS et flotte, doivent encore faire l’objet d’un audit de permissions. Tests PostgreSQL/Docker non réalisés ; ne pas déployer en production. Aucune migration exécutée.

# Boukoulou Transport V5.9 — PILOTE TECHNIQUE (ne pas déployer en production)

## Contenu
- `app/main.py` : intégration du routeur V5.9 et du comptage des embarquements.
- `app/v59.py` : tables, endpoints et règles V5.9.
- `app/models.py` et `app/schemas.py` : copies conservées de la V5.8.
- `ui/index.html`, `ui/js/app.js`, `ui/js/v59.js`, `ui/css/app.css` : interface adaptée.
- `migrations/v59.sql` : création de 3 tables sans suppression.

## Règles
ADMIN crée le stock ; AGENT vend des voyages en une transaction ; CONTROLLER valide un embarquement.
Un achat donne un QR unique, un compteur de voyages, et une expiration à la fin du mois d'achat
(fuseau Brazzaville/Libreville). Une ligne n'est autorisée que si son pays et son tarif sont identiques.
Chaque validation vérifie le solde et la capacité de la course avec verrous PostgreSQL.

## Limites importantes — NE PAS ENCAISSER DE VRAI ARGENT AVEC CETTE VERSION
- Le bouton d'encaissement est une **simulation d'une vente payée** : aucun terminal de paiement ni Mobile Money n'est connecté.
- Les ventes V5.9 sont stockées dans `v59_passes` ; les tableaux de bord et rapports de caisse historiques
  (`payments`, recettes par ligne, rapports de course) ne les intègrent PAS encore.
- Le vieux endpoint `POST /tickets` est désactivé (HTTP 410). Les billets V5.8 historiques restent conservés.
- Le vieux paiement `/tickets/{id}/payment` reste disponible pour les dossiers historiques ; il devra être fermé
  après régularisation des anciennes réservations.
- Le contrôle V5.9 dans l'interface ne lit que les nouveaux QR `BT-`. Le contrôle historique existe encore via Swagger.
- Pas encore de lecteur caméra QR ; le contenu CODE|SIGNATURE est collé dans le formulaire.
- Les tests automatisés et le test de concurrence réel sur PostgreSQL restent à réaliser.

## Installation uniquement sur une copie de test
1. Faire une sauvegarde complète de PostgreSQL, ainsi que des fichiers actuels.
2. Restaurer une copie de la base dans un environnement de test indépendant.
3. Sur cette copie, exécuter `migrations/v59.sql` avec psql.
4. Copier les fichiers aux emplacements indiqués (ajouter `app/v59.py` et `ui/js/v59.js`).
5. Exécuter `docker compose up -d --build --force-recreate api` puis consulter les logs.
6. Dans Swagger `/docs` : ADMIN `POST /v59/stocks`, AGENT `POST /v59/sales` avec caisse ouverte,
   CONTROLLER `POST /v59/boardings` avec `code`, `signature`, `trip_id`.
7. Vérifier les cas : mauvais pays, mauvais tarif, solde épuisé, mois expiré, bus plein, deux validations simultanées.

**Ne jamais lancer `docker compose down -v`.**

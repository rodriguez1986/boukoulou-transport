# Étape 5 — JWT et accès COUNTRY_MANAGER (reconstruction)

## Modifications
- Les nouveaux JWT portent `tv` (token_version).
- Chaque appel authentifié compare `tv` avec `users.token_version` ; un changement de rôle, de statut ou de mot de passe rend l'ancien jeton invalide.
- Les JWT précédents, sans `tv`, sont refusés : une reconnexion est nécessaire.
- `/auth/me` autorise COUNTRY_MANAGER et renvoie son country_id.
- Migration PostgreSQL additive proposée, **non exécutée**, dans `migrations/v59_country_manager_reconstruction.sql`.

## Contrôles effectués
- Analyse syntaxique des 11 modules Python : OK.
- Aucun test d'exécution FastAPI, PostgreSQL, Docker ou test de droits par requête HTTP n'a été réalisé.

## Points bloquants
- Les routes non auditées peuvent toujours exposer des données entre pays, notamment des routes publiques et financières. **Ne pas déployer.**
- L'interface JavaScript ne propose pas encore les pages adaptées à COUNTRY_MANAGER.
- Les anciens JWT seront invalidés par cette mise à jour.
- Le schéma PostgreSQL réel et le nom du type enum doivent être vérifiés avant toute migration.
- Les valeurs par défaut des mots de passe et JWT_SECRET doivent être remplacées avant tout déploiement.
- Aucun ancien jeu de données PostgreSQL n'est fourni.

## Suite
Étape 6 : tests isolés de l'authentification, revue route par route des droits et préparation d'un démarrage de test sur une base vierge uniquement.

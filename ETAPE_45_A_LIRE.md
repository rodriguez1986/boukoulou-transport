# Étape 45 — Préparation du contrôle d'accès côté API FastAPI

## Reconstitution
Tous les fichiers et fonctionnalités des étapes 1 à 44 sont conservés.

## Amélioration
Un routeur FastAPI de prévisualisation des autorisations a été ajouté :
`app/payment_api_step45.py`, chemin prévu
`POST /api/step45/payment-access/verifier`.

Le routeur dépend du JWT existant (`security.user`) qui vérifie l'identité,
le statut actif et la version du jeton. Il charge le pays affecté depuis
`User.country_id` et la table `Country`, puis applique la politique étape 44.
Les paramètres pays/canal/moyen/action sont validés **côté serveur**.

Correspondances prudentes : `AGENT` → caissier agence,
`DRIVER` → agent de bus, `COUNTRY_MANAGER` → superviseur,
`CONTROLLER` → auditeur. `ADMIN` ne reçoit aucun accès implicite
aux opérations de paiement. Aucun compte humain n'est assimilé à un PSP.

**Le routeur n'est PAS inclus dans `app/main.py` : il n'est donc pas
accessible sur l'API en cours.** Son activation nécessite revue des
rôles, des périmètres et des tests d'intégration d'authentification.

## Limites
L'endpoint ne fait que répondre si l'opération serait autorisée :
il ne confirme aucun paiement, ne crée aucun billet, n'appelle aucun PSP,
et n'écrit ni audit ni donnée financière. La réponse n'est pas un jeton
d'autorisation réutilisable pour une opération ultérieure. Les routes
financières existantes ne sont pas modifiées.

Les tests ciblés utilisent des doubles de DB et d'utilisateur ;
aucun serveur PostgreSQL réel n'est sollicité.

## Tests
`python -m pytest -q test_payment_api_step45.py test_payment_access_step44.py`

# Étape 37 — Contrat d'intégration PSP et plan de transaction

## Reconstitution
Tous les fichiers de l'étape 36 sont conservés.

## Amélioration
`app/psp_adapter_step37.py` propose :
- Une configuration explicite du fournisseur, de l'environnement et des prérequis de sécurité.
- Un diagnostic qui **refuse systématiquement l'activation** tant que l'intégration réelle n'est pas développée et testée.
- Un plan transactionnel PostgreSQL documentant unicité, verrouillage, idempotence et audit.

Le fichier `test_psp_adapter_step37.py` vérifie ces règles.

## Limites
Aucun prestataire (Airtel Money, MTN MoMo, Stripe, etc.) n'est supposé.
Le protocole HMAC de l'étape 35 est un **exemple**, pas une signature officielle.
Aucune route FastAPI, migration, connexion PSP, écriture PostgreSQL ni remboursement réel.
Ne pas déclarer cette étape prête pour la production.

## Suite
Choisir le PSP exact et obtenir sa documentation technique (signature webhook,
gestion des remboursements, identifiants, états, réponses HTTP). Puis implémenter
l'adaptateur réel en sandbox, avec tests d'intégration et base PostgreSQL de test.

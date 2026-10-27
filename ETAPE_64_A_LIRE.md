# Étape 64 — Clés de test JWT robustes

## Reconstitution
Toutes les étapes précédentes jusqu'à 63 sont conservées.

## Améliorations
- Les tests HTTP JWT de paiement utilisent des clés explicitement réservées aux tests, longues d'au moins 32 octets.
- Le test de signature incorrecte conserve une clé différente et longue, afin de vérifier réellement le refus des signatures invalides.
- Le test HTTP du rapport d'anomalies utilise lui aussi une clé incorrecte d'au moins 32 octets.
- Aucun changement de clé de production, d'API métier, de paiement réel ou de schéma de base.

## Vérification
Commande : `python -m pytest -q`
Résultat : 553 réussis, 12 ignorés, 2 avertissements (FastAPI `on_event` déprécié), 0 échec.
Les 23 avertissements PyJWT sur les clés trop courtes ont disparu.

## Limites
Les tests ignorés, l'absence de PostgreSQL réel et les avertissements FastAPI de démarrage restent à traiter. Aucun déploiement en production.

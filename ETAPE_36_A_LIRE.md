# Étape 36 — Réception simulée des notifications de remboursement

## Reconstitution
L'étape 35 et tous les fichiers précédents sont conservés.

## Amélioration
- `app/psp_reception_step36.py` assemble les contrôles **sans écriture** :
  1. Vérification HMAC sur les octets reçus (protocole de démonstration de l'étape 35).
  2. Décodage du JSON **uniquement après** vérification de la signature.
  3. Prévalidation du registre et recherche de doublons à partir d'un historique fourni.
- `test_psp_reception_step36.py` couvre signatures, contenu, doublons, conflits, références et montants.

## Attention : pas un webhook de production
Aucun endpoint réseau n'est exposé, aucune signature de prestataire réel n'est validée,
aucun événement n'est sauvegardé, aucun remboursement n'est exécuté.
La déduplication est seulement simulée sur un historique fourni : elle n'est pas
atomique en PostgreSQL et ne protège pas des notifications concurrentes.
Ne pas brancher ce module directement sur des notifications financières réelles.

## Vérification
`python -m pytest -q test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

## Étape suivante envisagée
Adapter le protocole au PSP réellement utilisé, puis concevoir une persistance
transactionnelle/idempotente avec migrations approuvées et tests PostgreSQL.

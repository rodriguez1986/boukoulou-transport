# Étape 39 — Parcours et états des paiements (simulation)

## Reconstitution
Conservation intégrale des fichiers de l'étape 38.

## Amélioration
Le module `app/payment_lifecycle_step39.py` simule le parcours de paiement d'un billet :
- Démarrage : **EN_ATTENTE** après contrôle du pays, canal, moyen et montant.
- États terminaux : **CONFIRME**, **ECHOUE**, **ANNULE**.
- En agence et dans le bus, seul l'acteur `CAISSIER` peut confirmer une simulation d'espèces.
- En ligne, seul `PSP_SIMULE` peut confirmer une simulation Mobile Money.
- Confirmation exige une référence ; aucun état terminal ne peut être changé à nouveau.
- Les objets de simulation sont immuables, sans modification de la base.

## Important
`CONFIRME` signifie **confirmé dans la simulation uniquement**. Aucun paiement réel,
aucune confirmation Airtel/MTN/Moov, aucun reçu ni billet émis, aucune route FastAPI,
aucune migration et aucune écriture PostgreSQL. Les règles d'autorisation réelles
et l'identité des agents restent à intégrer ; le simple libellé `CAISSIER` n'est
pas une authentification. Ce code ne doit pas être utilisé pour accepter des paiements.

## Vérification
`python -m pytest -q test_payment_lifecycle_step39.py test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

## Suite envisagée
Étape 40 : préparation d'un journal d'audit des intentions et transitions,
avec tests de cohérence et sans écriture en production.

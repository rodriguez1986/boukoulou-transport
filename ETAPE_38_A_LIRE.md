# Étape 38 — Moyens de paiement par pays et canal

## Règles métier confirmées
| Pays | Agence | Dans le bus | En ligne |
| --- | --- | --- | --- |
| République du Congo (CG, Congo-Brazzaville) | Espèces | Espèces | Airtel Money, MTN Mobile Money |
| Gabon (GA) | Espèces | Espèces | Airtel Money, Moov Money |

Les montants sont exprimés en francs CFA d'Afrique centrale (XAF), en unités entières positives.
Le pays est celui de la vente/agence concernée, à transmettre explicitement au module.

## Reconstitution
Le code des étapes précédentes est conservé, sans modification de la base.

## Amélioration
- `app/payment_routing_step38.py` : catalogue explicite des moyens autorisés,
  contrôle pays/canal/moyen/montant/devise, préparation d'une intention non persistée.
- `test_payment_routing_step38.py` : tests positifs et négatifs.
- Pas de moyens mobiles pour agence/bus, pas d'espèces en ligne.
- Les espèces requièrent une validation ultérieure par le caissier/agent ;
  les paiements en ligne exigent une confirmation ultérieure du prestataire.

## Limites impératives
Aucun débit, aucun encaissement, aucune API Airtel/MTN/Moov, aucun webhook réel,
aucune réservation payée, aucun reçu émis, aucune écriture PostgreSQL.
Les signatures et API exactes doivent être obtenues auprès des prestataires
et testées en sandbox avant mise en service. L'étape 37 continue de refuser
toute activation réelle. Ne pas utiliser cette étape comme moteur de paiement
en production.

## Tests
`python -m pytest -q test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

## Étape 39 proposée
Définir un parcours de paiement et ses statuts (intention, en attente,
confirmé, échoué, annulé), avec tests et sans intégration financière réelle.

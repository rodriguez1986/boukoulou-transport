# Étape 40 — Journal d’audit simulé des paiements

## Reconstitution
L'ensemble de l'étape 39 et des étapes antérieures est conservé.

## Amélioration
- `app/payment_audit_step40.py` : journal en mémoire avec numéro de séquence,
  acteur, pays, canal, moyen, montant XAF, référence du billet, état et
  empreinte SHA-256 chaînée.
- Refus de modifier un journal incohérent, de confirmer un état terminal,
  de changer de billet ou de canal pendant une transition.
- `test_payment_audit_step40.py` : tests des 8 combinaisons métier (Congo,
  Gabon, agence, bus, en ligne) et des refus de transition.

## Limites importantes
Le journal n'est **pas sauvegardé** : aucune table PostgreSQL, aucune
transaction, aucun appel API, aucun encaissement réel, aucun billet émis.
Le chaînage SHA-256 détecte les altérations accidentelles sans constituer une
preuve d'intégrité face à une personne capable de recalculer les empreintes.
Le journal doit être persisté transactionnellement, protégé par des droits,
une identité d'acteur vérifiée et des journaux d'infrastructure avant usage réel.

## Exécuter les tests ciblés
`python -m pytest -q test_payment_audit_step40.py test_payment_lifecycle_step39.py test_payment_routing_step38.py test_psp_adapter_step37.py test_psp_reception_step36.py test_psp_signature_step35.py test_refund_events_step33.py test_refund_event_ledger_step34.py`

## Étape 41 envisagée
Concevoir le stockage transactionnel des journaux en PostgreSQL, sans
l'activer en production avant revue de migration et tests d'intégration.

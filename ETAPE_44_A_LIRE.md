# Étape 44 — Contrôles d'accès aux opérations de paiement

## Reconstitution
Tous les fichiers des étapes précédentes sont conservés.

## Amélioration
`app/payment_access_step44.py` définit une politique de droits refusant par
défaut les opérations non autorisées, avec séparation des rôles :
- CAISSIER : agence, espèces, création / confirmation / annulation ;
- AGENT_BUS : bus, espèces, création / confirmation / annulation ;
- SUPERVISEUR : consultation d'audit et annulation selon son périmètre ;
- AUDITEUR : consultation uniquement ;
- SERVICE_PSP : réception de résultats Mobile Money **simulés** en ligne.

Le module vérifie aussi le pays, le canal et le moyen de paiement :
- Congo (CG) : espèces agence/bus, Airtel ou MTN en ligne ;
- Gabon (GA) : espèces agence/bus, Airtel ou Moov en ligne.

Les fonctions `verifier_autorisation` et `preparer_trace_decision` ne
réalisent aucune action réelle ni écriture en base.

## Limites de sécurité
L'indicateur `authentifiee=True` est une **donnée fournie par l'appelant** :
il ne constitue pas une authentification. En production, l'identité,
les rôles et les périmètres devront venir d'un service de confiance,
et la politique devra être appliquée au point d'entrée serveur, avant
l'exécution SQL. Ne jamais accepter ces attributs directement d'un client.

La trace produite est uniquement en mémoire : ni journal durable ni
horodatage de confiance. Aucun paiement réel n'est confirmé.
Les migrations PostgreSQL ne sont pas appliquées.

## Tests
`python -m pytest -q test_payment_access_step44.py`

## Vérification effectuée dans l'environnement de construction
190 tests ciblés des étapes 33–44 réussis, 3 tests PostgreSQL réels ignorés
faute de base de test. La suite complète `pytest` ne peut pas être collectée
ici car `passlib` (dépendance historique de `test_security_step6.py`) manque
dans cet environnement ; cela ne constitue pas un échec des tests ciblés.

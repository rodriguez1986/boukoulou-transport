# Étape 35 — Vérification cryptographique de notifications (protocole de test)

## Reconstitution
L'ensemble des fichiers de l'étape 34 est conservé.

## Amélioration
- `app/psp_signature_step35.py` : contrôle HMAC-SHA256 en temps constant (`hmac.compare_digest`) sur les **octets bruts**, avec horodatage signé et fenêtre de fraîcheur configurable.
- `test_psp_signature_step35.py` : tests des signatures valides, altérations, secrets incorrects, dates expirées, entrées malformées.

## Limites impératives
**Il s'agit d'un protocole de démonstration, pas de la vérification d'un vrai PSP.**
Le format exact des en-têtes, la construction du message signé, les algorithmes, le secret et la rotation des clés dépendent du prestataire choisi et doivent être implémentés selon sa documentation officielle. Ne pas connecter ce module directement à une API de remboursement réelle.

La vérification de la fenêtre temporelle ne remplace pas la **déduplication durable** (étape 34, migration toujours en brouillon), nécessaire contre les rejeux dans la fenêtre. Ne jamais enregistrer un événement, changer un état ou rembourser uniquement sur la base de ce résultat. Aucun changement PostgreSQL.

## Tests
`python -m pytest -q test_psp_signature_step35.py`

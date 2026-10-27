# Étape 57 — Retrait cohérent des affectations

## Reconstitution
L'intégralité des étapes 1 à 56 est conservée.

## Amélioration
- Le retrait verrouille maintenant l'employé, puis le voyage, puis l'affectation, dans le même ordre que l'attribution pour éviter les inversions de verrous PostgreSQL.
- Vérification après verrouillage que l'affectation n'a pas changé de voyage ou de bénéficiaire.
- Refus du retrait si le compte, le rôle ou le pays de l'employé n'est plus conforme (comportement conservé).
- Tests supplémentaires : réaffectation après retrait, affectations indépendantes, refus et audit inchangé en cas d'incohérence.

## Validation et limites
- Tests SQLite isolés et contrôles structurels ; pas de validation réelle des transactions concurrentes PostgreSQL.
- L'API étape 50 reste non montée. Aucune migration ni paiement réel.
- Aucune fonction de modification directe d'une affectation n'est exposée : la procédure reste retrait audité puis nouvelle attribution auditée.

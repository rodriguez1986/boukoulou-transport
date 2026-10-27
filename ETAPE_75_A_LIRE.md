# Boukoulou Transport V5.9 — Étape 75

## Objectif
Rejeter les JWT qui ne contiennent qu'un seul des champs `iat` ou `nbf`, afin d'empêcher le contournement du contrôle de durée de vie réelle.

## Modifications
- `app/security.py` : refuse un JWT si exactement un des champs `iat` et `nbf` est présent ; conserve la vérification chronologique et de durée de vie quand les deux sont présents.
- `test_jwt_pair_step75.py` : vérifie le rejet des champs isolés, le contrôle de durée, la compatibilité historique et les nouveaux jetons.

## Compatibilité et limites
Les anciens JWT sans **aucun** de ces deux champs restent acceptés jusqu'à expiration, sous réserve des autres contrôles. Leur durée de vie réelle ne peut pas être reconstituée. Une suppression de cette exception nécessiterait une décision explicite de migration. Aucun déploiement, migration ou rotation de clé n'a été effectué.

# Étape 58 — Cohérence des historiques d’affectation

## Reconstitution
Tous les fichiers des étapes 1 à 57 sont conservés.

## Amélioration
- Nouveau module `app/crew_assignment_audit_step58.py` : vérification en lecture seule des séquences ATTRIBUER/RETIRER, des identités, du voyage, du rôle et de l’état actif.
- Nouveau fichier de tests `test_crew_assignment_audit_step58.py` : attribution, retrait, réaffectation et détection de corruption simulée.
- Aucune modification directe d’affectation n’est exposée : le flux reste retrait audité puis nouvelle attribution auditée, **deux transactions distinctes**, sans atomicité globale garantie.

## Limites
- Un contrôle d'audit n'est pas une preuve cryptographique et ne protège pas contre une modification malveillante des deux tables.
- La vérification ne répare pas les données et n'est pas branchée aux routes de production.
- Tests PostgreSQL concurrents à exécuter séparément sur une base dédiée avant activation.

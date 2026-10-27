# Étape 82 — Limitation des tentatives de connexion

## Changements
- Protection de `/auth/login` : après 5 échecs pour un identifiant normalisé sur 15 minutes, refus temporaire pendant 15 minutes (`429`, `Retry-After: 900`).
- Les erreurs de connexion conservent le message générique `Identifiants invalides` et renvoient `401`.
- Réussite : remise à zéro des échecs de l'identifiant.
- Protection locale avec verrou thread-safe, horloge monotone et maximum de 10 000 identifiants en mémoire.
- Aucun mot de passe ou jeton n'est enregistré dans le limiteur.

## Limites avant production
- Stockage **en mémoire du processus** : les tentatives ne sont pas partagées entre workers/instances et disparaissent au redémarrage. Prévoir un stockage partagé atomique (Redis) et une limitation complémentaire par IP/segment réseau derrière un proxy correctement configuré.
- Une limite par identifiant peut être exploitée pour bloquer temporairement un compte ciblé. Prévoir une stratégie anti-abus, supervision et récupération de compte.
- Les différences de temps de calcul entre compte inexistant et existant restent possibles; une réponse générique ne garantit pas l'absence de fuite temporelle.
- Le `Retry-After` vaut 900 secondes, borne maximale indicative, et non le temps restant calculé.
- Aucun déploiement ni modification de base de données.

## Tests
`PYTHONPATH="$PWD/test_support_step53:$PWD" python -m pytest -q`

Résultat dans l'environnement de test : 775 passed, 10 skipped.

# Étape 66 — Fiabilité du démarrage et nettoyage des ressources

## Reconstitution
Conserve toutes les étapes précédentes jusqu'à l'étape 65.

## Modifications
- `app/main.py` : le seed optionnel exécute `rollback()` lorsqu'une lecture ou un `commit()` échoue, puis ferme toujours la session et propage l'erreur. Aucune exception n'est masquée.
- `test_lifespan_step66.py` : quatre tests pour la propagation des erreurs au démarrage, le rollback en cas d'échec de commit/lecture et les cycles de démarrage successifs sans ouverture de session lorsque le seed est désactivé.
- Aucune route supplémentaire, migration ou activation de production.

## Limites
Le cycle de vie des ressources externes PostgreSQL et des services de paiement n'est pas validé en environnement réel. Le `lifespan` ne détient pas lui-même de connexion permanente à fermer ; les sessions sont gérées par leurs fonctions propriétaires.

# Boukoulou Transport V5.9 — Étape 76

## Objectif
Renforcer la protection contre les dates `iat` et `nbf` artificiellement anciennes.

## Modifications
- `app/security.py` : contrôle complémentaire de fraîcheur des deux dates par rapport à l'horloge du serveur, avec tolérance de 2 secondes pour l'arrondi des timestamps.
- `test_jwt_old_dates_step76.py` : tests de dates anciennes, jetons récents, paire incomplète et compatibilité historique.

## Compatibilité et limites
Le contrôle de durée signée (`exp - iat` et `exp - nbf`) reste en place. Les JWT historiques dépourvus des deux champs continuent d'être acceptés jusqu'à leur expiration, sous réserve des autres contrôles : leur ancienneté réelle n'est pas vérifiable. Le contrôle de fraîcheur est une défense complémentaire et ne remplace pas les contrôles de signature, d'expiration et de révocation. Aucun déploiement, migration ni rotation de clé.

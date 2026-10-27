# Étape 47 — Chauffeur et contrôleur : mêmes droits à bord

## Reconstitution
Conservation de toutes les étapes 1 à 46.

## Amélioration
- `CONTROLLER` reçoit les mêmes permissions de **simulation** d'encaissement
  en espèces dans le bus que `DRIVER`, via `app/payment_api_step45.py`.
- Politique de contrôle d'embarquement `app/boarding_access_step47.py` :
  consulter voyage et passagers, contrôler un billet, valider l'embarquement.
- Exigence d'une affectation active et vérifiée par un composant serveur,
  liée à l'utilisateur, au voyage et au pays.
- Les agents, responsables nationaux et administrateurs ne reçoivent pas
  automatiquement ces droits d'embarquement.

## Limites importantes
Le modèle existant ne relie pas de manière fiable `User` à `Driver` ni
`CONTROLLER` à un voyage : **la preuve d'affectation n'est pas encore
implémentée**. La dataclass `AffectationVerifiee` n'est PAS une preuve de
confiance si elle provient du client. Ne jamais exposer directement ce
contrôle avec un booléen `source_verifiee` fourni par le navigateur.

Le contrôle d'embarquement est une politique non branchée à l'API.
Le routeur de paiement de l'étape 45 reste non monté dans `main.py`.
Aucun paiement réel, aucune validation de billet, aucune migration,
aucune écriture en base de production.

## Tests
`python -m pytest -q test_boarding_access_step47.py test_payment_controller_step47.py`

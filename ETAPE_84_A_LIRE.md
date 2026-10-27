# Étape 84 — Protection complémentaire par IP

- Après 20 échecs de connexion provenant d'une même IP sur une fenêtre de 15 minutes, toute nouvelle tentative provenant de cette IP reçoit HTTP 429.
- Ce compteur s'ajoute au compteur par identifiant (ou couple identifiant/IP en mode Redis), sans remplacer les limites existantes.
- Une connexion réussie n'efface pas le compteur IP, afin de limiter les attaques réparties sur plusieurs comptes.
- Mode Redis : compteur atomique partagé entre processus. Sans Redis : mémoire locale, non partagée entre workers.
- Les en-têtes `X-Forwarded-For` fournis directement par le client sont ignorés ; configurer correctement le proxy inverse de confiance pour que `request.client.host` reflète la bonne IP.
- Attention aux réseaux NAT partagés : plusieurs utilisateurs peuvent avoir la même IP et être limités collectivement. Le seuil doit être ajusté et surveillé avant production.
- Aucun déploiement ni changement de base de données.

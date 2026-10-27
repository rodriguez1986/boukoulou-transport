# Boukoulou Transport

MVP exécutable de gestion de transport urbain multi-pays.

## Fonctionnalités
- Congo-Brazzaville et Gabon préchargés
- JWT + rôles ADMIN/CONTROLLER/DRIVER
- lignes, véhicules, courses
- tickets et QR signés HMAC
- paiement simulé
- contrôle anti-double-utilisation
- dashboard
- GPS, maintenance, carburant
- PostgreSQL + Docker
- test d'intégration du parcours complet

## Lancer avec Docker
```bash
docker compose up --build
```
Puis ouvrir `http://localhost:8000/docs`.

Compte initial : `admin / REPLACE_WITH_STRONG_ADMIN_PASSWORD` (développement uniquement). Changez-le en production.

## Test local
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

## Paiement/WhatsApp réels
Le simulateur fonctionne sans fournisseur externe. Pour MTN/Airtel/WhatsApp, il faut brancher les API officielles et secrets du compte marchand ; aucune fausse URL ou clé n'est intégrée.

"""Smoke HTTP réel, SQLite mémoire, aucun démarrage réseau ni migration."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['BOUKOULOU_ENABLE_DEV_SEED'] = '0'
os.environ['JWT_SECRET'] = 'step18-test-only-not-for-production'

from fastapi.testclient import TestClient
from app.main import app

with TestClient(app) as client:
    health = client.get('/health')
    assert health.status_code == 200, (health.status_code, health.text)
    assert health.json().get('status') == 'ok', health.text
    print('OK GET /health : 200')

    # Token volontairement invalide : rejet AVANT toute requête SQL.
    auth = {'Authorization': 'Bearer invalid-test-token'}
    me = client.get('/auth/me', headers=auth)
    assert me.status_code == 401, (me.status_code, me.text)
    print('OK GET /auth/me (JWT invalide) : 401')

    cash = client.post('/cash/sessions/open', json={'opening_amount': 0}, headers=auth)
    assert cash.status_code == 401, (cash.status_code, cash.text)
    print('OK POST /cash/sessions/open (JWT invalide) : 401')

print('Smoke HTTP terminé. Aucune migration ni écriture en base.')

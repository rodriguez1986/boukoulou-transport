"""Vrais appels HTTP JWT avec DB simulée, sans table ni PostgreSQL."""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['BOUKOULOU_ENABLE_DEV_SEED'] = '0'
os.environ['JWT_SECRET'] = 'step19-isolated-test-secret-only'

import jwt
from fastapi.testclient import TestClient
from app.main import app
from app.db import get_db
from app.models import Role

state = {'role': Role.DRIVER, 'active': True, 'version': 2, 'exists': True}

class FakeDB:
    def get(self, model, identifier):
        if not state['exists'] or int(identifier) != 101:
            return None
        return SimpleNamespace(id=101, username='step19', role=state['role'],
                               is_active=state['active'], token_version=state['version'],
                               country_id=None)

def fake_db():
    yield FakeDB()

def make_token(version=2, expired=False):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=-1 if expired else 15)
    return jwt.encode({'sub':'101','tv':version,'exp':expiry},
                      os.environ['JWT_SECRET'],algorithm='HS256')

def request(client, path, version=2, expired=False, method='get'):
    headers={'Authorization':f'Bearer {make_token(version,expired)}'}
    if method == 'post':
        return client.post(path,headers=headers,json={'opening_amount':0})
    return client.get(path,headers=headers)

app.dependency_overrides[get_db] = fake_db
try:
    with TestClient(app) as client:
        state.update(role=Role.DRIVER,active=True,version=2,exists=True)
        response=request(client,'/auth/me')
        assert response.status_code == 200,(response.status_code,response.text)
        assert response.json()['role'] == 'DRIVER'
        print('OK JWT valide /auth/me : 200')

        response=request(client,'/cash/sessions/open',method='post')
        assert response.status_code == 403,(response.status_code,response.text)
        print('OK DRIVER caisse : 403 (aucune requête SQL métier)')

        response=request(client,'/auth/me',version=1)
        assert response.status_code == 401,(response.status_code,response.text)
        print('OK JWT version révoquée : 401')

        response=request(client,'/auth/me',expired=True)
        assert response.status_code == 401,(response.status_code,response.text)
        print('OK JWT expiré : 401')

        state['active']=False
        response=request(client,'/auth/me')
        assert response.status_code == 401,(response.status_code,response.text)
        print('OK utilisateur désactivé : 401')

        state.update(active=True,exists=False)
        response=request(client,'/auth/me')
        assert response.status_code == 401,(response.status_code,response.text)
        print('OK utilisateur absent : 401')
finally:
    app.dependency_overrides.pop(get_db,None)
print('Tests JWT terminés : aucune table créée, aucune migration exécutée.')

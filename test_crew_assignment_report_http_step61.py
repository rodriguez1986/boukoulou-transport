"""Tests HTTP réels de l'API étape 60, sans montage dans app.main.

Si passlib n'est pas installé, un shim strictement réservé aux tests permet
l'import de security.py. Aucune méthode de hachage n'est simulée.
"""
import importlib.util
import sys
from pathlib import Path
if importlib.util.find_spec('passlib') is None:
    sys.path.insert(0, str(Path(__file__).parent / 'test_support_step53'))

from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db import Base, get_db
from app.models import User, Role, Country, Line, Trip, Vehicle
from app.security import token, SECRET
from app.crew_assignment_step48 import CrewAssignmentStep48
from app.crew_assignment_admin_step49 import CrewAssignmentAuditStep49
from app.crew_assignment_report_api_step60 import router

PATH = '/api/step60/crew-assignment-anomalies'

@pytest.fixture
def env():
    engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as db:
        cg = Country(code='CG', name='Congo', currency='XAF')
        ga = Country(code='GA', name='Gabon', currency='XAF')
        db.add_all([cg, ga]); db.flush()
        lc = Line(country_id=cg.id, code='61CG', name='CG', fare=1000)
        lg = Line(country_id=ga.id, code='61GA', name='GA', fare=1000)
        db.add_all([lc, lg]); db.flush()
        vc = Vehicle(country_id=cg.id, code='61VC', plate='61-CG', capacity=40)
        vg = Vehicle(country_id=ga.id, code='61VG', plate='61-GA', capacity=40)
        db.add_all([vc, vg]); db.flush()
        tc = Trip(line_id=lc.id, vehicle_id=vc.id, departure_at=datetime.now(timezone.utc))
        tg = Trip(line_id=lg.id, vehicle_id=vg.id, departure_at=datetime.now(timezone.utc))
        db.add_all([tc, tg]); db.flush()
        users = {}
        for name, role, country in [('admin', Role.ADMIN, None), ('manager_cg', Role.COUNTRY_MANAGER, cg),
                                    ('manager_ga', Role.COUNTRY_MANAGER, ga), ('driver', Role.DRIVER, cg),
                                    ('agent', Role.AGENT, cg), ('inactive', Role.ADMIN, None),
                                    ('no_country', Role.COUNTRY_MANAGER, None)]:
            u = User(username='s61_'+name, password_hash='unused', role=role,
                     country_id=country.id if country else None, is_active=name != 'inactive', token_version=0)
            db.add(u); db.flush(); users[name] = u.id
        now = datetime.now(timezone.utc)
        # Trois affectations volontairement sans audit : trois anomalies détectables.
        for trip in (tc, tg, tc):
            db.add(CrewAssignmentStep48(user_id=users['driver'], trip_id=trip.id,
                    role='DRIVER', active=True, starts_at=now, ends_at=now+timedelta(hours=1),
                    assigned_by_user_id=users['admin']))
        db.commit()
        ids = {'trip_cg': tc.id, 'trip_ga': tg.id, **users}
    app = FastAPI()
    app.include_router(router)
    def isolated_db():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = isolated_db
    with TestClient(app) as client:
        def headers(name):
            with Session() as db:
                return {'Authorization': 'Bearer ' + token(db.get(User, ids[name]))}
        yield client, Session, ids, headers
    engine.dispose()

def test_missing_token_is_rejected(env):
    client, *_ = env
    assert client.get(PATH).status_code in (401, 403)

def test_invalid_signature_rejected(env):
    client, _, ids, _ = env
    forged = jwt.encode({'sub': str(ids['admin']), 'tv': 0,
                         'exp': datetime.now(timezone.utc)+timedelta(hours=1)},
                        'step64-invalid-report-signature-test-key-32-bytes-minimum', algorithm='HS256')
    assert client.get(PATH, headers={'Authorization':'Bearer '+forged}).status_code == 401

def test_expired_token_rejected(env):
    client, _, ids, _ = env
    expired = jwt.encode({'sub': str(ids['admin']), 'tv': 0,
                          'exp': datetime.now(timezone.utc)-timedelta(minutes=1)}, SECRET, algorithm='HS256')
    assert client.get(PATH, headers={'Authorization':'Bearer '+expired}).status_code == 401

def test_admin_sees_both_countries(env):
    client, _, _, headers = env
    r = client.get(PATH, headers=headers('admin'))
    assert r.status_code == 200, r.text
    assert r.json()['scanned'] == 3 and r.json()['anomaly_count'] == 3

def test_manager_country_scoping(env):
    client, _, ids, headers = env
    cg = client.get(PATH, headers=headers('manager_cg'))
    ga = client.get(PATH, headers=headers('manager_ga'))
    assert cg.status_code == ga.status_code == 200
    assert cg.json()['scanned'] == 2 and ga.json()['scanned'] == 1
    assert all(a['trip_id'] == ids['trip_cg'] for a in cg.json()['anomalies'])
    assert all(a['trip_id'] == ids['trip_ga'] for a in ga.json()['anomalies'])

def test_forbidden_roles_and_missing_country(env):
    client, _, _, headers = env
    for role in ('driver', 'agent', 'no_country'):
        assert client.get(PATH, headers=headers(role)).status_code == 403

def test_inactive_user_rejected(env):
    client, _, _, headers = env
    assert client.get(PATH, headers=headers('inactive')).status_code == 401

def test_revoked_token_version_rejected(env):
    client, Session, ids, headers = env
    old = headers('admin')
    with Session() as db:
        u = db.get(User, ids['admin']); u.token_version += 1; db.commit()
    assert client.get(PATH, headers=old).status_code == 401

def test_pagination_and_country_scope(env):
    client, _, ids, headers = env
    r1 = client.get(PATH, headers=headers('manager_cg'), params={'limit': 1})
    assert r1.status_code == 200 and r1.json()['has_more'] is True
    assert r1.json()['scanned'] == 1
    r2 = client.get(PATH, headers=headers('manager_cg'),
                    params={'limit': 1, 'after_id': r1.json()['next_after_id']})
    assert r2.status_code == 200 and r2.json()['scanned'] == 1
    assert r2.json()['has_more'] is False
    assert all(a['trip_id'] == ids['trip_cg'] for r in (r1,r2) for a in r.json()['anomalies'])

@pytest.mark.parametrize('params', [{'limit': 0}, {'limit': 501}, {'limit': 'abc'},
                                     {'after_id': -1}, {'after_id': 'abc'}])
def test_invalid_query_returns_422(env, params):
    client, _, _, headers = env
    assert client.get(PATH, headers=headers('admin'), params=params).status_code == 422

def test_report_does_not_write(env):
    client, Session, _, headers = env
    with Session() as db:
        before = (db.query(CrewAssignmentStep48).count(), db.query(CrewAssignmentAuditStep49).count())
    assert client.get(PATH, headers=headers('admin')).status_code == 200
    with Session() as db:
        assert (db.query(CrewAssignmentStep48).count(), db.query(CrewAssignmentAuditStep49).count()) == before

def test_main_app_still_does_not_mount_router():
    source = (Path(__file__).parent / 'app' / 'main.py').read_text()
    assert 'crew_assignment_report_api_step60' not in source

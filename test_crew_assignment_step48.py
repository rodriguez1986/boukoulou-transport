from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from app.db import Base
from app.models import Country, Line, Trip, User, Driver, Vehicle
from app.crew_assignment_step48 import CrewAssignmentStep48, verifier_acces_voyage
from app.boarding_access_step47 import VALIDER_EMBARQUEMENT, CONTROLER_BILLET

NOW = datetime(2026, 10, 24, 15, tzinfo=timezone.utc)

@pytest.fixture
def db():
    engine = create_engine('sqlite+pysqlite:///:memory:')
    @event.listens_for(engine, 'connect')
    def fk_on(conn, record):
        conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([Country(id=1,code='CG',name='Congo',currency='XAF'),
                   Country(id=2,code='GA',name='Gabon',currency='XAF')])
        s.flush()
        s.add(Line(id=1,country_id=1,code='BZV-PNR',name='Test',fare=1000))
        s.add(Line(id=2,country_id=2,code='LBV',name='Test GA',fare=1000))
        s.add(Vehicle(id=1,country_id=1,code='B1',plate='TEST1',capacity=40))
        s.add(Driver(id=1,country_id=1,employee_code='D1',first_name='A',last_name='B',license_number='LIC1'))
        s.flush()
        s.add_all([Trip(id=1,line_id=1,vehicle_id=1,driver_id=1,departure_at=NOW),
                   Trip(id=2,line_id=2,vehicle_id=1,driver_id=1,departure_at=NOW)])
        from app.models import Role
        for uid, role in [(1,Role.DRIVER),(2,Role.CONTROLLER),(3,Role.AGENT),(4,Role.ADMIN)]:
            s.add(User(id=uid,username=f'u{uid}',password_hash='unused',role=role,
                       is_active=True,token_version=0,country_id=1))
        s.flush()
        for uid, role in [(1,'DRIVER'),(2,'CONTROLLER'),(3,'AGENT')]:
            s.add(CrewAssignmentStep48(user_id=uid,trip_id=1,role=role,
                 active=True,starts_at=NOW-timedelta(hours=1),
                 ends_at=NOW+timedelta(hours=2),assigned_by_user_id=4))
        s.commit()
        yield s
    engine.dispose()

def check(db, uid=1, tid=1, now=NOW, action=VALIDER_EMBARQUEMENT):
    return verifier_acces_voyage(db,user_id=uid,trip_id=tid,action=action,maintenant=now)

@pytest.mark.parametrize('uid', [1,2])
@pytest.mark.parametrize('action', [VALIDER_EMBARQUEMENT,CONTROLER_BILLET])
def test_bord_autorise(db,uid,action):
    r=check(db,uid,action=action)
    assert r['autorise'] and not r['embarquement_enregistre']

def test_agent_interdit(db):
    assert not check(db,3)['autorise']

def test_admin_interdit(db):
    assert not check(db,4)['autorise']

def test_voyage_non_affecte(db):
    assert not check(db,1,2)['autorise']

def test_affectation_expiree(db):
    assert not check(db,1,now=NOW+timedelta(hours=3))['autorise']

def test_affectation_future(db):
    assert not check(db,1,now=NOW-timedelta(hours=3))['autorise']

def test_compte_desactive(db):
    u=db.get(User,1); u.is_active=False; db.flush()
    assert not check(db)['autorise']

def test_pays_different(db):
    u=db.get(User,1); u.country_id=2; db.flush()
    assert not check(db)['autorise']

def test_affectation_inactive(db):
    a=db.query(CrewAssignmentStep48).filter_by(user_id=1).one(); a.active=False; db.flush()
    assert not check(db)['autorise']

def test_role_affectation_incoherent(db):
    a=db.query(CrewAssignmentStep48).filter_by(user_id=1).one(); a.role='CONTROLLER'; db.flush()
    assert not check(db)['autorise']

def test_utilisateur_inexistant(db):
    assert not check(db,999)['autorise']

def test_action_inconnue(db):
    assert not check(db,action='MODIFIER_TARIF')['autorise']

def test_date_naive_refusee(db):
    assert not check(db,now=datetime(2026,10,24))['autorise']

def test_sql_non_applique():
    from pathlib import Path
    migration=Path(__file__).parent/'migrations'/'v59_crew_assignments_step48_DRAFT_NOT_APPLIED.sql'
    assert migration.exists()
    assert 'CREATE TABLE' in migration.read_text()

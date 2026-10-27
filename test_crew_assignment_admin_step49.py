from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from app.db import Base
from app.models import Country, Line, Trip, User, Driver, Vehicle, Role
from app.crew_assignment_step48 import CrewAssignmentStep48, verifier_acces_voyage
from app.crew_assignment_admin_step49 import (
    CrewAssignmentAuditStep49, AffectationRefusee, attribuer, retirer, consulter,
)
from app.boarding_access_step47 import VALIDER_EMBARQUEMENT

NOW = datetime(2026, 10, 24, 15, tzinfo=timezone.utc)

@pytest.fixture
def db():
    engine = create_engine('sqlite+pysqlite:///:memory:')
    @event.listens_for(engine, 'connect')
    def fk_on(conn, record): conn.execute('PRAGMA foreign_keys=ON')
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        s.add_all([Country(id=1, code='CG', name='Congo', currency='XAF'),
                   Country(id=2, code='GA', name='Gabon', currency='XAF')])
        s.flush()
        s.add_all([Line(id=1, country_id=1, code='CG-L', name='CG', fare=1000),
                   Line(id=2, country_id=2, code='GA-L', name='GA', fare=1000)])
        s.add(Vehicle(id=1, country_id=1, code='BUS49', plate='TEST49', capacity=40))
        s.add(Driver(id=1, country_id=1, employee_code='D49', first_name='A',last_name='B',license_number='LIC49'))
        s.flush()
        s.add_all([Trip(id=1, line_id=1, vehicle_id=1, driver_id=1, departure_at=NOW),
                   Trip(id=2, line_id=2, vehicle_id=1, driver_id=1, departure_at=NOW)])
        for uid, role, country in [(1, Role.ADMIN, None), (2, Role.COUNTRY_MANAGER, 1),
                                   (3, Role.COUNTRY_MANAGER, 2), (4, Role.DRIVER, 1),
                                   (5, Role.CONTROLLER, 1), (6, Role.AGENT, 1),
                                   (7, Role.DRIVER, 2)]:
            s.add(User(id=uid, username=f'step49_{uid}', password_hash='unused',
                       role=role, is_active=True, token_version=0, country_id=country))
        s.commit()
        yield s
    engine.dispose()

def assign(db, **kw):
    args = dict(actor_id=2, target_user_id=4, trip_id=1,
                starts_at=NOW-timedelta(hours=1), ends_at=NOW+timedelta(hours=2), maintenant=NOW)
    args.update(kw)
    return attribuer(db, **args)

def test_attribuer_et_audit(db):
    aid=assign(db)
    assert db.get(CrewAssignmentStep48, aid).role == 'DRIVER'
    audit=db.scalars(select(CrewAssignmentAuditStep49)).one()
    assert (audit.action, audit.actor_id, audit.target_user_id) == ('ATTRIBUER', 2, 4)
    assert consulter(db, actor_id=2, trip_id=1)[0]['id'] == aid
    assert verifier_acces_voyage(db, user_id=4, trip_id=1,
                                 action=VALIDER_EMBARQUEMENT, maintenant=NOW)['autorise']

def test_controleur(db):
    aid=assign(db,target_user_id=5)
    assert db.get(CrewAssignmentStep48,aid).role == 'CONTROLLER'

def test_retirer_et_audit(db):
    aid=assign(db)
    assert retirer(db,actor_id=2,assignment_id=aid,maintenant=NOW)
    assert not db.get(CrewAssignmentStep48,aid).active
    assert [a.action for a in db.scalars(select(CrewAssignmentAuditStep49).order_by(CrewAssignmentAuditStep49.id))] == ['ATTRIBUER','RETIRER']
    assert not verifier_acces_voyage(db,user_id=4,trip_id=1,
                                      action=VALIDER_EMBARQUEMENT,maintenant=NOW)['autorise']

def test_doublon_chevauchant_refuse(db):
    assign(db)
    with pytest.raises(AffectationRefusee,match='CHEVAUCHANTE'):assign(db)
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all())==1

def test_intervalles_non_chevauchants(db):
    assign(db)
    aid=assign(db, starts_at=NOW+timedelta(hours=2),ends_at=NOW+timedelta(hours=3))
    assert aid > 0

@pytest.mark.parametrize('actor', [4,5,6,7])
def test_role_admin_refuse(db,actor):
    with pytest.raises(AffectationRefusee):assign(db,actor_id=actor)

@pytest.mark.parametrize('actor,trip', [(2,2),(3,1)])
def test_manager_autre_pays_refuse(db,actor,trip):
    with pytest.raises(AffectationRefusee,match='PAYS_HORS_PERIMETRE'):
        assign(db,actor_id=actor,trip_id=trip)

def test_admin_global(db):
    assert assign(db,actor_id=1)>0

def test_agent_pas_affectable(db):
    with pytest.raises(AffectationRefusee,match='ROLE_CIBLE_INTERDIT'):
        assign(db,target_user_id=6)

def test_cible_autre_pays(db):
    with pytest.raises(AffectationRefusee,match='CIBLE_HORS_PERIMETRE'):
        assign(db,target_user_id=7)

def test_compte_inactif(db):
    u=db.get(User,4);u.is_active=False;db.commit()
    with pytest.raises(AffectationRefusee):assign(db)

def test_date_naive(db):
    with pytest.raises(AffectationRefusee,match='DATE_INVALIDE'):
        assign(db,starts_at=datetime(2026,10,24))

def test_periode_invalide(db):
    with pytest.raises(AffectationRefusee,match='PERIODE_INVALIDE'):
        assign(db,ends_at=NOW-timedelta(hours=2))

def test_retrait_double_refuse(db):
    aid=assign(db)
    retirer(db,actor_id=2,assignment_id=aid)
    with pytest.raises(AffectationRefusee,match='DEJA_RETIREE'):
        retirer(db,actor_id=2,assignment_id=aid)
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all())==2

def test_retrait_hors_pays_refuse(db):
    aid=assign(db)
    with pytest.raises(AffectationRefusee,match='PAYS_HORS_PERIMETRE'):
        retirer(db,actor_id=3,assignment_id=aid)
    assert db.get(CrewAssignmentStep48,aid).active

def test_consultation_hors_pays_refuse(db):
    with pytest.raises(AffectationRefusee):consulter(db,actor_id=3,trip_id=1)

def test_consultation_agent_refuse(db):
    with pytest.raises(AffectationRefusee):consulter(db,actor_id=6,trip_id=1)

def test_aucune_route_activee():
    from pathlib import Path
    main=(Path(__file__).parent/'app'/'main.py').read_text(encoding='utf-8')
    assert 'crew_assignment_admin_step49' not in main

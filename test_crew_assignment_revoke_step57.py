"""Régression retrait, cohérence et ordre des verrous, sans base réelle."""
from datetime import timedelta
from sqlalchemy import select
from app.models import User, Role
from app.crew_assignment_step48 import CrewAssignmentStep48
from app.crew_assignment_admin_step49 import CrewAssignmentAuditStep49, AffectationRefusee, retirer
from test_crew_assignment_admin_step49 import db, assign, NOW
import pytest


def test_retrait_permet_nouvelle_affectation_chevauchante(db):
    first = assign(db)
    assert retirer(db, actor_id=2, assignment_id=first, maintenant=NOW)
    second = assign(db, trip_id=1)
    assert second != first
    assert not db.get(CrewAssignmentStep48, first).active
    assert db.get(CrewAssignmentStep48, second).active
    assert [a.action for a in db.scalars(select(CrewAssignmentAuditStep49).order_by(CrewAssignmentAuditStep49.id))] == ['ATTRIBUER', 'RETIRER', 'ATTRIBUER']


def test_retrait_ne_desactive_pas_autres_affectations(db):
    first = assign(db)
    second = assign(db, starts_at=NOW+timedelta(hours=2), ends_at=NOW+timedelta(hours=4))
    retirer(db, actor_id=2, assignment_id=first)
    assert db.get(CrewAssignmentStep48, second).active
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all()) == 3


def test_retrait_refuse_apres_changement_role_sans_audit(db):
    aid = assign(db)
    u = db.get(User, 4)
    u.role = Role.AGENT
    db.commit()
    with pytest.raises(AffectationRefusee, match='ROLE_CIBLE_INTERDIT'):
        retirer(db, actor_id=2, assignment_id=aid)
    assert db.get(CrewAssignmentStep48, aid).active
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all()) == 1


def test_retrait_refuse_apres_changement_pays_sans_audit(db):
    aid = assign(db)
    u = db.get(User, 4)
    u.country_id = 2
    db.commit()
    with pytest.raises(AffectationRefusee, match='CIBLE_HORS_PERIMETRE'):
        retirer(db, actor_id=2, assignment_id=aid)
    assert db.get(CrewAssignmentStep48, aid).active
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all()) == 1


def test_retrait_refuse_apres_desactivation_compte(db):
    aid = assign(db)
    u = db.get(User, 4)
    u.is_active = False
    db.commit()
    with pytest.raises(AffectationRefusee, match='CIBLE_HORS_PERIMETRE'):
        retirer(db, actor_id=2, assignment_id=aid)
    assert db.get(CrewAssignmentStep48, aid).active
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all()) == 1


def test_retrait_refuse_autre_responsable_pays(db):
    aid = assign(db)
    with pytest.raises(AffectationRefusee, match='PAYS_HORS_PERIMETRE'):
        retirer(db, actor_id=3, assignment_id=aid)
    assert db.get(CrewAssignmentStep48, aid).active


def test_verrouillage_retrait_user_avant_trip_et_assignment():
    from pathlib import Path
    src = (Path(__file__).parent / 'app' / 'crew_assignment_admin_step49.py').read_text()
    block = src.split('def retirer(', 1)[1].split('def consulter(', 1)[0]
    assert block.index('select(User.id)') < block.index('select(Trip.id)') < block.index('select(CrewAssignmentStep48)')
    assert "AFFECTATION_MODIFIEE" in block

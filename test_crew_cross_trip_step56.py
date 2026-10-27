"""Non-chevauchement des affectations d'un employé entre voyages distincts."""
from datetime import timedelta
from sqlalchemy import select
import pytest
from app.models import Trip
from app.crew_assignment_step48 import CrewAssignmentStep48
from app.crew_assignment_admin_step49 import AffectationRefusee, attribuer, CrewAssignmentAuditStep49
from test_crew_assignment_admin_step49 import db, NOW


def assign(db, trip_id, start, end, target=4):
    return attribuer(db, actor_id=2, target_user_id=target, trip_id=trip_id,
                    starts_at=start, ends_at=end, maintenant=NOW)


def second_trip(db):
    db.add(Trip(id=3, line_id=1, vehicle_id=1, driver_id=1, departure_at=NOW + timedelta(hours=1)))
    db.commit()


def test_meme_employe_deux_voyages_chevauchants_refuses(db):
    second_trip(db)
    assign(db, 1, NOW, NOW + timedelta(hours=3))
    with pytest.raises(AffectationRefusee, match='CHEVAUCHANTE'):
        assign(db, 3, NOW + timedelta(hours=1), NOW + timedelta(hours=4))
    assert len(db.scalars(select(CrewAssignmentStep48)).all()) == 1
    assert len(db.scalars(select(CrewAssignmentAuditStep49)).all()) == 1


def test_meme_employe_voyages_successifs_autorises(db):
    second_trip(db)
    assign(db, 1, NOW, NOW + timedelta(hours=2))
    assign(db, 3, NOW + timedelta(hours=2), NOW + timedelta(hours=3))
    assert len(db.scalars(select(CrewAssignmentStep48)).all()) == 2


def test_roles_distincts_sur_deux_voyages_autorises(db):
    second_trip(db)
    assign(db, 1, NOW, NOW + timedelta(hours=3), target=4)
    assign(db, 3, NOW, NOW + timedelta(hours=3), target=5)
    assert len(db.scalars(select(CrewAssignmentStep48)).all()) == 2


def test_periode_ouverte_interdit_autre_voyage(db):
    second_trip(db)
    assign(db, 1, NOW, None)
    with pytest.raises(AffectationRefusee, match='CHEVAUCHANTE'):
        assign(db, 3, NOW + timedelta(days=1), None)


def test_verrou_employe_avant_voyage():
    from pathlib import Path
    src = (Path(__file__).parent / 'app' / 'crew_assignment_admin_step49.py').read_text()
    assert src.index('select(User.id).where(User.id == target.id).with_for_update()') < src.index('select(Trip.id).where(Trip.id == trip_id).with_for_update()')
    assert 'CrewAssignmentStep48.trip_id == trip.id' not in src.split('def attribuer(',1)[1].split('def retirer(',1)[0]

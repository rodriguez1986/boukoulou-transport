"""Tests isolés du rapport administratif en lecture seule."""
import pytest
from sqlalchemy import select
from test_crew_assignment_admin_step49 import db, assign, NOW
from app.crew_assignment_admin_step49 import CrewAssignmentAuditStep49, retirer
from app.crew_assignment_report_step59 import rapport_anomalies_affectations


def test_rapport_vide(db):
    assert rapport_anomalies_affectations(db) == {
        'scanned': 0, 'anomaly_count': 0, 'anomalies': [],
        'has_more': False, 'next_after_id': 0,
    }


def test_rapport_sain(db):
    aid = assign(db)
    result = rapport_anomalies_affectations(db)
    assert result['scanned'] == 1
    assert result['anomaly_count'] == 0
    assert result['next_after_id'] == aid


def test_rapport_detecte_anomalie_sans_reparer(db):
    aid = assign(db)
    audit = db.scalars(select(CrewAssignmentAuditStep49)).one()
    audit.role = 'CONTROLLER'
    db.flush()
    result = rapport_anomalies_affectations(db)
    assert result['anomaly_count'] == 1
    assert result['anomalies'][0]['assignment_id'] == aid
    assert 'DONNEES_AUDIT_DIVERGENTES' in result['anomalies'][0]['codes']
    assert audit.role == 'CONTROLLER'


def test_rapport_pagination_compte_affectations_pas_anomalies(db):
    first = assign(db)
    retirer(db, actor_id=2, assignment_id=first, maintenant=NOW)
    second = assign(db)
    result = rapport_anomalies_affectations(db, limit=1)
    assert result['scanned'] == 1
    assert result['has_more'] is True
    assert result['next_after_id'] == first
    following = rapport_anomalies_affectations(db, limit=1, after_id=first)
    assert following['scanned'] == 1
    assert following['next_after_id'] == second
    assert following['has_more'] is False


@pytest.mark.parametrize('limit', [0, -1, 501, True, 1.5, '10', None])
def test_limite_invalide(db, limit):
    with pytest.raises(ValueError, match='LIMITE_INVALIDE'):
        rapport_anomalies_affectations(db, limit=limit)


@pytest.mark.parametrize('cursor', [-1, True, 1.2, '1', None])
def test_curseur_invalide(db, cursor):
    with pytest.raises(ValueError, match='CURSEUR_INVALIDE'):
        rapport_anomalies_affectations(db, after_id=cursor)

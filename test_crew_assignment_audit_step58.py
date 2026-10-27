"""Contrôles d'audit isolés sur les fixtures de l'étape 49."""
import pytest
from sqlalchemy import select
from test_crew_assignment_admin_step49 import db, assign, NOW
from app.crew_assignment_admin_step49 import retirer, CrewAssignmentAuditStep49
from app.crew_assignment_audit_step58 import verifier_integrite_audits
from app.crew_assignment_step48 import CrewAssignmentStep48


def test_attribution_audit_coherent(db):
    aid = assign(db)
    assert verifier_integrite_audits(db, assignment_id=aid) == ()


def test_retrait_audit_coherent(db):
    aid = assign(db)
    retirer(db, actor_id=2, assignment_id=aid, maintenant=NOW)
    assert verifier_integrite_audits(db, assignment_id=aid) == ()


def test_reaffectation_apres_retrait_audit_independant(db):
    aid = assign(db)
    retirer(db, actor_id=2, assignment_id=aid, maintenant=NOW)
    other = assign(db)
    assert verifier_integrite_audits(db, assignment_id=aid) == ()
    assert verifier_integrite_audits(db, assignment_id=other) == ()


def test_audit_divergent_detecte(db):
    aid = assign(db)
    audit = db.scalars(select(CrewAssignmentAuditStep49)).one()
    audit.role = 'CONTROLLER'
    db.flush()
    assert 'DONNEES_AUDIT_DIVERGENTES' in verifier_integrite_audits(db, assignment_id=aid)


def test_audit_manquant_detecte(db):
    aid = assign(db)
    audit = db.scalars(select(CrewAssignmentAuditStep49)).one()
    db.delete(audit)
    db.flush()
    issues = verifier_integrite_audits(db, assignment_id=aid)
    assert 'ATTRIBUTION_ABSENTE' in issues


def test_etat_incoherent_detecte(db):
    aid = assign(db)
    db.get(CrewAssignmentStep48, aid).active = False
    db.flush()
    assert 'ETAT_RETIRE_INCOHERENT' in verifier_integrite_audits(db, assignment_id=aid)


@pytest.mark.parametrize('bad', [0, -1, True, '1', None])
def test_identifiant_invalide(db, bad):
    with pytest.raises(ValueError, match='AFFECTATION_INVALIDE'):
        verifier_integrite_audits(db, assignment_id=bad)


def test_identifiant_inconnu(db):
    with pytest.raises(ValueError, match='AFFECTATION_INCONNUE'):
        verifier_integrite_audits(db, assignment_id=9999)

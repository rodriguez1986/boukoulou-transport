"""Contrôle en lecture seule de la cohérence des journaux d’affectations.

Ce contrôle ne répare ni ne modifie les données et ne remplace pas une
contrainte transactionnelle PostgreSQL. Appeler sur une session de confiance.
"""
from sqlalchemy import select
from .crew_assignment_step48 import CrewAssignmentStep48
from .crew_assignment_admin_step49 import CrewAssignmentAuditStep49


def verifier_integrite_audits(db, *, assignment_id):
    """Retourne des codes d'anomalie stables; aucun commit, aucune écriture."""
    if type(assignment_id) is not int or assignment_id <= 0:
        raise ValueError('AFFECTATION_INVALIDE')
    assignment = db.get(CrewAssignmentStep48, assignment_id)
    if assignment is None:
        raise ValueError('AFFECTATION_INCONNUE')
    events = db.scalars(select(CrewAssignmentAuditStep49).where(
        CrewAssignmentAuditStep49.assignment_id == assignment_id
    ).order_by(CrewAssignmentAuditStep49.id)).all()
    problems = []
    if not events or events[0].action != 'ATTRIBUER':
        problems.append('ATTRIBUTION_ABSENTE')
    expected = 'ATTRIBUER'
    for event in events:
        if event.action != expected:
            problems.append('SEQUENCE_INCOHERENTE')
        expected = 'RETIRER' if event.action == 'ATTRIBUER' else 'ATTRIBUER'
        if (event.target_user_id != assignment.user_id or
                event.trip_id != assignment.trip_id or event.role != assignment.role):
            problems.append('DONNEES_AUDIT_DIVERGENTES')
    if assignment.active and (not events or events[-1].action != 'ATTRIBUER'):
        problems.append('ETAT_ACTIF_INCOHERENT')
    if not assignment.active and (not events or events[-1].action != 'RETIRER'):
        problems.append('ETAT_RETIRE_INCOHERENT')
    return tuple(dict.fromkeys(problems))

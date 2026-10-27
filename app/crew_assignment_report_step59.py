"""Rapport de cohérence des affectations (lecture seule, non exposé en API).

Appeler uniquement depuis un contexte administratif de confiance. La fonction
n'effectue aucune réparation, aucune écriture ni commit.
"""
from sqlalchemy import select
from .crew_assignment_step48 import CrewAssignmentStep48
from .models import Trip, Line
from .crew_assignment_audit_step58 import verifier_integrite_audits


def rapport_anomalies_affectations(db, *, limit=100, after_id=0, country_id=None):
    """Page déterministe des anomalies, avec pagination par identifiant.

    `scanned` compte les affectations examinées dans la page, et `next_after_id`
    permet de continuer sans confondre nombre d'anomalies et taille de page.
    """
    if type(limit) is not int or not 1 <= limit <= 500:
        raise ValueError('LIMITE_INVALIDE')
    if type(after_id) is not int or after_id < 0:
        raise ValueError('CURSEUR_INVALIDE')
    if country_id is not None and (type(country_id) is not int or country_id <= 0):
        raise ValueError("PAYS_INVALIDE")
    query = select(CrewAssignmentStep48).where(CrewAssignmentStep48.id > after_id)
    if country_id is not None:
        query = (query.join(Trip, CrewAssignmentStep48.trip_id == Trip.id)
                 .join(Line, Trip.line_id == Line.id)
                 .where(Line.country_id == country_id))
    rows = db.scalars(query.order_by(CrewAssignmentStep48.id).limit(limit + 1)).all()
    page = rows[:limit]
    anomalies = []
    for assignment in page:
        codes = verifier_integrite_audits(db, assignment_id=assignment.id)
        if codes:
            anomalies.append({
                'assignment_id': assignment.id,
                'user_id': assignment.user_id,
                'trip_id': assignment.trip_id,
                'codes': list(codes),
            })
    return {
        'scanned': len(page),
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
        'has_more': len(rows) > limit,
        'next_after_id': page[-1].id if page else after_id,
    }

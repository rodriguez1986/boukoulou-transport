"""Moteur de lecture des recettes Boukoulou Transport V5.9.

Ce module ne modifie aucune transaction. Les montants des ventes à bord
proviennent de la colonne calculée total_amount dans PostgreSQL.
"""
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.models import Line, Trip
from app.v59 import Pass59, OnboardSale59, Boarding59

CASH_TZ = ZoneInfo("Africa/Brazzaville")


def _bornes_jour(jour: date):
    """Convertir les limites d'une journée locale en instants UTC."""
    debut = datetime(jour.year, jour.month, jour.day, tzinfo=CASH_TZ)
    fin = debut + timedelta(days=1)
    return debut.astimezone(timezone.utc), fin.astimezone(timezone.utc)


def _transactions(db: Session, jour: date, agent_id: int | None = None):
    """Construire une seule transaction par pass, sans double comptage.

    Les passes guichet n'ont pas de course garantie. Les ventes à bord
    portent explicitement un trip_id. Les embarquements ne sont pas des ventes.
    """
    debut, fin = _bornes_jour(jour)
    passes_query = db.query(Pass59).filter(Pass59.sold_at >= debut, Pass59.sold_at < fin)
    if agent_id is not None:
        passes_query = passes_query.filter(Pass59.agent_id == agent_id)
    passes = passes_query.all()
    if not passes:
        return []

    ids = [p.id for p in passes]
    ventes_bord = {
        vente.pass_id: vente
        for vente in db.query(OnboardSale59).filter(OnboardSale59.pass_id.in_(ids)).all()
    }
    course_ids = {vente.trip_id for vente in ventes_bord.values()}
    courses = {
        course.id: course
        for course in db.query(Trip).filter(Trip.id.in_(course_ids)).all()
    } if course_ids else {}
    ligne_ids = {course.line_id for course in courses.values()}
    lignes = {
        ligne.id: ligne
        for ligne in db.query(Line).filter(Line.id.in_(ligne_ids)).all()
    } if ligne_ids else {}

    resultat = []
    for p in passes:
        vente = ventes_bord.get(p.id)
        course = courses.get(vente.trip_id) if vente else None
        ligne = lignes.get(course.line_id) if course else None
        # Une vente à bord remplace le total du pass, elle ne s'y ajoute pas.
        montant = int(vente.total_amount if vente else p.total)
        resultat.append({
            "payment_id": p.id,  # Alias de compatibilité avec l'ancien frontend.
            "transaction_type": "ONBOARD" if vente else "COUNTER",
            "user_id": p.agent_id,
            "operator_id": vente.controller_id if vente else p.agent_id,
            "cash_session_id": vente.cash_session_id if vente else p.cash_session_id,
            "reference": p.reference,
            "provider": p.provider,
            "amount": montant,
            "transport_amount": int(vente.transport_amount if vente else p.total),
            "onboard_fee": int(vente.onboard_fee) if vente else 0,
            "printing_fee": int(vente.printing_fee) if vente else 0,
            "payment_status": "SUCCESS",  # Vente persistée, pas confirmation externe.
            "paid_at": p.sold_at,
            "ticket_id": p.id,
            "ticket_code": p.code,
            "quantity": int(p.quantity),
            "trip_id": course.id if course else None,
            "departure_at": course.departure_at if course else None,
            "line_id": ligne.id if ligne else None,
            "line_code": ligne.code if ligne else None,
            "line_name": ligne.name if ligne else None,
        })
    resultat.sort(key=lambda x: x["paid_at"], reverse=True)
    return resultat


def caisse_jour(db: Session, jour: date, agent_id: int | None = None):
    """Retourner les compteurs, recettes et ventilations de la journée."""
    transactions = _transactions(db, jour, agent_id)
    providers = defaultdict(lambda: {"payments": 0, "revenue": 0})
    for t in transactions:
        p = providers[t["provider"]]
        p["payments"] += 1
        p["revenue"] += t["amount"]
    return {
        "date": jour.isoformat(),
        "timezone": "Africa/Brazzaville",
        "payments_success": len(transactions),
        "tickets_sold": sum(t["quantity"] for t in transactions),
        "trips_collected": len({t["trip_id"] for t in transactions if t["trip_id"] is not None}),
        "revenue": sum(t["amount"] for t in transactions),
        "transport_revenue": sum(t["transport_amount"] for t in transactions),
        "onboard_fees": sum(t["onboard_fee"] for t in transactions),
        "printing_fees": sum(t["printing_fee"] for t in transactions),
        "providers": [{"provider": nom, **valeurs} for nom, valeurs in sorted(providers.items())],
    }


def caisse_details(db: Session, jour: date, agent_id: int | None = None):
    """Afficher les transactions de la journée, une ligne par vente."""
    return _transactions(db, jour, agent_id)


def caisse_par_ligne(db: Session, jour: date, agent_id: int | None = None):
    """Agréger les ventes dont la ligne est connue sans attribution fictive."""
    groupes = {}
    for t in _transactions(db, jour, agent_id):
        if t["line_id"] is None:
            continue
        identifiant = t["line_id"]
        if identifiant not in groupes:
            groupes[identifiant] = {
                "line_id": identifiant, "line_code": t["line_code"],
                "line_name": t["line_name"], "tickets": 0, "revenue": 0,
            }
        groupes[identifiant]["tickets"] += t["quantity"]
        groupes[identifiant]["revenue"] += t["amount"]
    return sorted(groupes.values(), key=lambda r: r["revenue"], reverse=True)


def caisse_par_course(db: Session, jour: date, agent_id: int | None = None):
    """Agréger les ventes associées explicitement à une course."""
    groupes = {}
    for t in _transactions(db, jour, agent_id):
        if t["trip_id"] is None:
            continue
        identifiant = t["trip_id"]
        if identifiant not in groupes:
            groupes[identifiant] = {
                "trip_id": identifiant, "departure_at": t["departure_at"],
                "line_code": t["line_code"], "line_name": t["line_name"],
                "tickets": 0, "revenue": 0,
            }
        groupes[identifiant]["tickets"] += t["quantity"]
        groupes[identifiant]["revenue"] += t["amount"]
    return sorted(groupes.values(), key=lambda r: r["departure_at"], reverse=True)


def caisse_par_operateur(db: Session, jour: date, agent_id: int | None = None):
    """Agréger les encaissements par vendeur ou contrôleur responsable."""
    groupes = {}
    for t in _transactions(db, jour, agent_id):
        identifiant = t["operator_id"]
        if identifiant not in groupes:
            groupes[identifiant] = {"operator_id": identifiant, "payments": 0, "revenue": 0}
        groupes[identifiant]["payments"] += 1
        groupes[identifiant]["revenue"] += t["amount"]
    return sorted(groupes.values(), key=lambda r: r["revenue"], reverse=True)

"""Affectations de bord, lecture seule, non branchées aux routes réelles.

Les affectations doivent être attribuées par un responsable habilité après
vérification opérationnelle. Ce module n'accepte aucun booléen de confiance
provenant d'une requête HTTP.
"""
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, DateTime, Boolean, String, select, or_
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import Country, Line, Trip, User
from .boarding_access_step47 import AffectationVerifiee, autoriser_embarquement


class CrewAssignmentStep48(Base):
    __tablename__ = "bt_crew_assignments_step48"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)


def verifier_acces_voyage(db, *, user_id, trip_id, action, maintenant=None):
    """Reconstitue le contexte uniquement depuis la base, refuse par défaut.

    Le résultat n'est pas une autorisation réutilisable pour une écriture future.
    Toute écriture réelle devra revérifier l'affectation dans sa transaction.
    """
    refus = {"autorise": False, "motifs": ("AFFECTATION_NON_VERIFIEE",),
             "operation_executee": False, "billet_valide": False,
             "embarquement_enregistre": False}
    if type(user_id) is not int or user_id <= 0 or type(trip_id) is not int or trip_id <= 0:
        return refus
    instant = maintenant if maintenant is not None else datetime.now(timezone.utc)
    if not isinstance(instant, datetime) or instant.tzinfo is None or instant.utcoffset() is None:
        return refus
    utilisateur = db.get(User, user_id)
    voyage = db.get(Trip, trip_id)
    if utilisateur is None or voyage is None:
        return refus
    ligne = db.get(Line, voyage.line_id)
    pays_utilisateur = db.get(Country, utilisateur.country_id) if utilisateur.country_id is not None else None
    pays_voyage = db.get(Country, ligne.country_id) if ligne is not None else None
    if pays_utilisateur is None or pays_voyage is None:
        return refus
    role = getattr(utilisateur.role, "value", utilisateur.role)
    # Ne pas considérer la seule affectation chauffeur historique comme une
    # preuve du lien User→Driver : elle n'est pas établie dans le schéma.
    affectations = db.scalars(select(CrewAssignmentStep48).where(
        CrewAssignmentStep48.user_id == user_id,
        CrewAssignmentStep48.trip_id == trip_id,
        CrewAssignmentStep48.role == role,
        CrewAssignmentStep48.active.is_(True),
        CrewAssignmentStep48.starts_at <= instant,
        or_(CrewAssignmentStep48.ends_at.is_(None),
            CrewAssignmentStep48.ends_at > instant),
    )).all()
    valide = bool(affectations)
    contexte = AffectationVerifiee(
        user_id=user_id, voyage_id=trip_id, pays=pays_voyage.code,
        affectation_active=valide, source_verifiee=True,
    )
    return autoriser_embarquement(
        user_id=user_id, role=role, actif=utilisateur.is_active,
        pays_utilisateur=pays_utilisateur.code, voyage_id=trip_id,
        pays_voyage=pays_voyage.code, action=action, affectation=contexte,
    )

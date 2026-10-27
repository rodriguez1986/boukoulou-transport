"""Administration des affectations de bord — service non branché à l’API.

Appeler avec une session DB de confiance et un actor_id issu du JWT vérifié.
Chaque commande verrouille les lignes nécessaires, écrit un audit et commit
ensemble; ne pas exposer les arguments directement à un client HTTP.
"""
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, String, DateTime, select, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base
from .models import User, Trip, Line, Country, Role
from .crew_assignment_step48 import CrewAssignmentStep48


class CrewAssignmentAuditStep49(Base):
    __tablename__ = "bt_crew_assignment_audit_step49"
    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("bt_crew_assignments_step48.id"), nullable=False)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    target_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (CheckConstraint("action IN ('ATTRIBUER','RETIRER')", name="ck_crew_audit_action_step49"),)


class AffectationRefusee(ValueError):
    pass


def _refuser(message):
    raise AffectationRefusee(message)


def _role(user):
    return getattr(user.role, 'value', user.role)


def _contexte(db, actor_id, trip_id):
    if type(actor_id) is not int or actor_id <= 0 or type(trip_id) is not int or trip_id <= 0:
        _refuser('PARAMETRES_INVALIDES')
    actor = db.get(User, actor_id)
    trip = db.get(Trip, trip_id)
    if actor is None or not actor.is_active or trip is None:
        _refuser('CONTEXTE_INVALIDE')
    line = db.get(Line, trip.line_id)
    country = db.get(Country, line.country_id) if line is not None else None
    if country is None or country.code not in ('CG', 'GA'):
        _refuser('PAYS_INVALIDE')
    role = _role(actor)
    if role not in (Role.ADMIN.value, Role.COUNTRY_MANAGER.value):
        _refuser('ROLE_ADMIN_INTERDIT')
    # ADMIN est global, COUNTRY_MANAGER strictement limité à son pays.
    if role == Role.COUNTRY_MANAGER.value and actor.country_id != country.id:
        _refuser('PAYS_HORS_PERIMETRE')
    return actor, trip, country


def _target(db, target_user_id, country_id):
    if type(target_user_id) is not int or target_user_id <= 0:
        _refuser('CIBLE_INVALIDE')
    user = db.get(User, target_user_id)
    if user is None or not user.is_active or user.country_id != country_id:
        _refuser('CIBLE_HORS_PERIMETRE')
    role = _role(user)
    if role not in (Role.DRIVER.value, Role.CONTROLLER.value):
        _refuser('ROLE_CIBLE_INTERDIT')
    return user, role


def _instant(value):
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _refuser('DATE_INVALIDE')
    return value


def attribuer(db, *, actor_id, target_user_id, trip_id, starts_at, ends_at=None, maintenant=None):
    """Crée une affectation + audit atomiquement; aucun paiement ni embarquement."""
    try:
        now = _instant(maintenant or datetime.now(timezone.utc))
        start = _instant(starts_at)
        end = _instant(ends_at) if ends_at is not None else None
        if end is not None and end <= start:
            _refuser('PERIODE_INVALIDE')
        actor, trip, country = _contexte(db, actor_id, trip_id)
        target, role = _target(db, target_user_id, country.id)
        # Verrouiller d'abord l'employé : toutes les affectations de ce compte,
        # même sur des voyages différents, sont sérialisées sur PostgreSQL.
        # Ordre stable : User puis Trip (évite une inversion entre créations).
        db.execute(select(User.id).where(User.id == target.id).with_for_update()).scalar_one()
        db.execute(select(Trip.id).where(Trip.id == trip_id).with_for_update()).scalar_one()
        existing = db.scalars(select(CrewAssignmentStep48).where(
            CrewAssignmentStep48.user_id == target.id,
            CrewAssignmentStep48.active.is_(True),
        ).with_for_update()).all()
        # SQLite restitue souvent les timestamps sans tzinfo ; normaliser
        # uniquement pour la comparaison, sans changer les données stockées.
        def utc_naive(value):
            if value is None:
                return None
            return (value.astimezone(timezone.utc).replace(tzinfo=None)
                    if value.tzinfo is not None else value)
        for old in existing:
            # Chevauchement de périodes semi-ouvertes [start, end).
            if (end is None or utc_naive(old.starts_at) < utc_naive(end)) and (old.ends_at is None or utc_naive(start) < utc_naive(old.ends_at)):
                _refuser('AFFECTATION_CHEVAUCHANTE')
        assignment = CrewAssignmentStep48(
            user_id=target.id, trip_id=trip.id, role=role, active=True,
            starts_at=start, ends_at=end, assigned_by_user_id=actor.id)
        db.add(assignment)
        db.flush()
        db.add(CrewAssignmentAuditStep49(
            assignment_id=assignment.id, actor_id=actor.id,
            target_user_id=target.id, trip_id=trip.id, action='ATTRIBUER',
            role=role, happened_at=now))
        db.commit()
        return assignment.id
    except Exception:
        db.rollback()
        raise


def retirer(db, *, actor_id, assignment_id, maintenant=None):
    """Désactive l'affectation et journalise l'acteur dans la même transaction."""
    try:
        now = _instant(maintenant or datetime.now(timezone.utc))
        if type(assignment_id) is not int or assignment_id <= 0:
            _refuser('AFFECTATION_INVALIDE')
        assignment = db.get(CrewAssignmentStep48, assignment_id)
        if assignment is None:
            _refuser('AFFECTATION_INCONNUE')
        # Même ordre de verrous que l'attribution : User -> Trip -> Assignment.
        # Une attribution concurrente sur un autre voyage du même employé
        # attend la fin du retrait, et inversement.
        target_user_id = assignment.user_id
        trip_id = assignment.trip_id
        db.execute(select(User.id).where(User.id == target_user_id).with_for_update()).scalar_one()
        actor, trip, country = _contexte(db, actor_id, trip_id)
        db.execute(select(Trip.id).where(Trip.id == trip.id).with_for_update()).scalar_one()
        assignment = db.scalars(select(CrewAssignmentStep48).where(
            CrewAssignmentStep48.id == assignment_id).with_for_update()).one()
        if assignment.user_id != target_user_id or assignment.trip_id != trip_id:
            _refuser('AFFECTATION_MODIFIEE')
        if not assignment.active:
            _refuser('AFFECTATION_DEJA_RETIREE')
        # Refuser les incohérences de pays ou de rôle même pour une révocation.
        target, role = _target(db, assignment.user_id, country.id)
        if role != assignment.role:
            _refuser('ROLE_AFFECTATION_INCOHERENT')
        assignment.active = False
        db.add(CrewAssignmentAuditStep49(
            assignment_id=assignment.id, actor_id=actor.id,
            target_user_id=target.id, trip_id=trip.id, action='RETIRER',
            role=role, happened_at=now))
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def consulter(db, *, actor_id, trip_id):
    """Liste uniquement les affectations du voyage dans le périmètre autorisé."""
    _contexte(db, actor_id, trip_id)
    rows = db.scalars(select(CrewAssignmentStep48).where(
        CrewAssignmentStep48.trip_id == trip_id
    ).order_by(CrewAssignmentStep48.id)).all()
    return tuple({"id": a.id, "user_id": a.user_id, "role": a.role,
                  "active": a.active, "starts_at": a.starts_at,
                  "ends_at": a.ends_at} for a in rows)

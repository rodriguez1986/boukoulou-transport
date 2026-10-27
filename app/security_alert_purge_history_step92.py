"""Historique SQL des purges planifiées, sans données sensibles.

Nécessite l'application manuelle de la migration étape 92.
"""
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, SessionLocal


class SecurityAlertPurgeRun(Base):
    __tablename__ = 'security_alert_purge_runs'
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    dry_run: Mapped[bool] = mapped_column(nullable=False)
    deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    eligible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)


ALLOWED_STATUSES = {'completed', 'skipped_locked', 'failed'}


def record(*, status, dry_run, batch_size, deleted=0, eligible=0, error_code=None):
    if status not in ALLOWED_STATUSES:
        raise ValueError('Statut invalide')
    if type(dry_run) is not bool or type(batch_size) is not int or not 1 <= batch_size <= 1000:
        raise ValueError('Paramètres invalides')
    if type(deleted) is not int or type(eligible) is not int or deleted < 0 or eligible < 0:
        raise ValueError('Compteurs invalides')
    # Code d'erreur technique seulement, jamais exception/SQL/identifiant brut.
    if error_code is not None and (not isinstance(error_code, str) or error_code not in {'PURGE_FAILED', 'AUDIT_FAILED'}):
        raise ValueError('Code d’erreur invalide')
    with SessionLocal() as session:
        row = SecurityAlertPurgeRun(started_at=datetime.now(timezone.utc), status=status,
            dry_run=dry_run, batch_size=batch_size, deleted=deleted, eligible=eligible, error_code=error_code)
        session.add(row)
        session.commit()
        session.refresh(row)
        return row.id


def recent(limit=50, before_id=None):
    if type(limit) is not int or not 1 <= limit <= 200:
        raise ValueError('Limite invalide')
    if before_id is not None and (type(before_id) is not int or before_id < 1):
        raise ValueError('Curseur invalide')
    stmt = select(SecurityAlertPurgeRun)
    if before_id is not None:
        stmt = stmt.where(SecurityAlertPurgeRun.id < before_id)
    with SessionLocal() as session:
        rows = session.scalars(stmt.order_by(SecurityAlertPurgeRun.id.desc()).limit(limit)).all()
        return [{'id': r.id, 'started_at': r.started_at.replace(tzinfo=timezone.utc).isoformat() if r.started_at.tzinfo is None else r.started_at.isoformat(),
                 'status': r.status, 'dry_run': r.dry_run, 'deleted': r.deleted, 'eligible': r.eligible,
                 'batch_size': r.batch_size, 'error_code': r.error_code} for r in rows]

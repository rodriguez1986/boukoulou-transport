"""Purge manuelle, bornée et vérifiable des alertes SQL (aucune tâche automatique)."""
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete, func, select
from .security_alert_storage_step89 import SecurityLoginAlert, SessionLocal

DEFAULT_RETENTION_DAYS = 90
MAX_BATCH = 1000


def retention_days():
    raw = os.getenv('BOUKOULOU_SECURITY_ALERT_RETENTION_DAYS', str(DEFAULT_RETENTION_DAYS))
    try:
        days = int(raw)
    except (ValueError, TypeError) as exc:
        raise ValueError('Durée de conservation invalide') from exc
    if not 1 <= days <= 3650:
        raise ValueError('Durée de conservation attendue : 1 à 3650 jours')
    return days


def purge(*, dry_run=True, now=None, batch_size=500):
    """Retourne un bilan. Supprime au maximum batch_size lignes par appel."""
    if type(dry_run) is not bool:
        raise ValueError('dry_run doit être booléen')
    if type(batch_size) is not int or not 1 <= batch_size <= MAX_BATCH:
        raise ValueError('batch_size doit être entre 1 et 1000')
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('now doit inclure un fuseau horaire')
    cutoff = now.astimezone(timezone.utc) - timedelta(days=retention_days())
    with SessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(SecurityLoginAlert).where(SecurityLoginAlert.occurred_at < cutoff))
        result = {'dry_run': dry_run, 'cutoff_utc': cutoff.isoformat(), 'eligible': count, 'deleted': 0, 'batch_size': batch_size}
        if dry_run or not count:
            return result
        ids = session.scalars(select(SecurityLoginAlert.id).where(SecurityLoginAlert.occurred_at < cutoff).order_by(SecurityLoginAlert.id).limit(batch_size)).all()
        if ids:
            result['deleted'] = session.execute(delete(SecurityLoginAlert).where(SecurityLoginAlert.id.in_(ids))).rowcount
            session.commit()
        return result

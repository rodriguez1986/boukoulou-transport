"""Stockage SQL optionnel des alertes; schéma à migrer explicitement avant activation."""
import os
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base, SessionLocal

class SecurityLoginAlert(Base):
    __tablename__ = 'security_login_alerts'
    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True, autoincrement=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    event: Mapped[str] = mapped_column(String(60), nullable=False)
    component: Mapped[str] = mapped_column(String(60), nullable=False)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)
    ref: Mapped[str] = mapped_column(String(128), nullable=False)
    count: Mapped[int] = mapped_column(Integer, nullable=False)
    window_seconds: Mapped[int] = mapped_column(Integer, nullable=False)

def enabled():
    return os.getenv('BOUKOULOU_SECURITY_ALERT_STORAGE', '').strip().lower() == 'database'

def store(alert):
    if alert.get('event') != 'login_failure_burst' or alert.get('scope') not in ('user_ref', 'client_ref'):
        return
    # Liste blanche : jamais de mot de passe, IP ou identifiant en clair.
    with SessionLocal() as session:
        session.add(SecurityLoginAlert(
            occurred_at=datetime.now(timezone.utc), event='login_failure_burst',
            component='auth.login', scope=alert['scope'], ref=alert['ref'],
            count=int(alert['count']), window_seconds=int(alert['window_seconds'])))
        session.commit()

def recent(limit=50, *, scope=None, since=None, until=None, before_id=None):
    from .security_alert_registry_step87 import VALID_SCOPES, MAX_ALERTS
    if scope is not None and scope not in VALID_SCOPES:
        raise ValueError('Portée inconnue')
    if since is not None and (since.tzinfo is None or since.utcoffset() is None):
        raise ValueError('since doit inclure un fuseau horaire')
    if until is not None and (until.tzinfo is None or until.utcoffset() is None):
        raise ValueError('until doit inclure un fuseau horaire')
    if since is not None and until is not None and since > until:
        raise ValueError('since doit précéder until')
    if before_id is not None and before_id < 1:
        raise ValueError('before_id doit être positif')
    query = select(SecurityLoginAlert)
    if scope is not None: query = query.where(SecurityLoginAlert.scope == scope)
    if since is not None: query = query.where(SecurityLoginAlert.occurred_at >= since)
    if until is not None: query = query.where(SecurityLoginAlert.occurred_at <= until)
    if before_id is not None: query = query.where(SecurityLoginAlert.id < before_id)
    query = query.order_by(SecurityLoginAlert.id.desc()).limit(max(1, min(int(limit), MAX_ALERTS)))
    with SessionLocal() as session:
        rows = session.execute(query).scalars().all()
        return [{'id': a.id, 'occurred_at': a.occurred_at.replace(tzinfo=timezone.utc).isoformat() if a.occurred_at.tzinfo is None else a.occurred_at.isoformat(),
                 'event': a.event, 'component': a.component, 'scope': a.scope, 'ref': a.ref,
                 'count': a.count, 'window_seconds': a.window_seconds} for a in rows]

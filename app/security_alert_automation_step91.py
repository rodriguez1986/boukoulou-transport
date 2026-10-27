"""Exécution planifiée externe, explicite et verrouillée de la purge SQL."""
import os
from sqlalchemy import text
from . import security_alert_retention_step90 as retention
from . import security_alert_purge_history_step92 as history
from . import security_alert_purge_notify_step93 as notifications

LOCK_ID = 91890091  # Verrou consultatif PostgreSQL dédié à cette tâche.


def run_scheduled(*, apply=False, batch_size=500):
    """Ne programme rien: invocation depuis cron/systemd, une seule passe bornée."""
    if os.getenv('BOUKOULOU_SECURITY_ALERT_STORAGE', '').strip().lower() != 'database':
        raise ValueError('Stockage SQL des alertes non activé')
    if os.getenv('BOUKOULOU_SECURITY_ALERT_AUTO_PURGE', '').strip().lower() != 'enabled':
        raise ValueError('Purge planifiée non activée')
    if type(apply) is not bool:
        raise ValueError('apply doit être booléen')
    if type(batch_size) is not int or not 1 <= batch_size <= retention.MAX_BATCH:
        raise ValueError('Taille de lot invalide')
    # Refuser tout autre moteur : le verrou distribué PostgreSQL est requis.
    with retention.SessionLocal() as session:
        if session.get_bind().dialect.name != 'postgresql':
            raise ValueError('Purge planifiée réservée à PostgreSQL')
        acquired = bool(session.scalar(text('SELECT pg_try_advisory_lock(:key)'), {'key': LOCK_ID}))
        if not acquired:
            history.record(status='skipped_locked', dry_run=not apply, batch_size=batch_size)
            return {'status': 'skipped_locked', 'deleted': 0}
        try:
            # La connexion porteuse du verrou reste ouverte pendant la purge.
            result = retention.purge(dry_run=not apply, batch_size=batch_size)
            history.record(status='completed', dry_run=not apply, batch_size=batch_size,
                           deleted=result.get('deleted', 0), eligible=result.get('eligible', 0))
            return {'status': 'completed', **result}
        except Exception:
            try:
                history.record(status='failed', dry_run=not apply, batch_size=batch_size, error_code='PURGE_FAILED')
            except Exception:
                pass  # Le processus retourne une erreur, même si l'audit est indisponible.
            try:
                notifications.notify_failure(error_code='PURGE_FAILED')
            except Exception:
                # L’échec SMTP ne masque jamais l’échec initial de purge.
                pass
            raise
        finally:
            session.scalar(text('SELECT pg_advisory_unlock(:key)'), {'key': LOCK_ID})

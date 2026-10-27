from datetime import datetime, timedelta, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import security_alert_retention_step90 as retention
from app import security_alert_storage_step89 as storage


def test_retention_dry_run_and_batched_purge(monkeypatch, tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "retention.sqlite"}')
    storage.SecurityLoginAlert.__table__.create(engine)
    factory = sessionmaker(bind=engine)
    monkeypatch.setattr(retention, 'SessionLocal', factory)
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_RETENTION_DAYS', '30')
    now = datetime(2026, 10, 25, tzinfo=timezone.utc)
    with factory() as session:
        for age in (60, 45, 10):
            session.add(storage.SecurityLoginAlert(occurred_at=now-timedelta(days=age), event='login_failure_burst', component='auth.login', scope='user_ref', ref='hash', count=10, window_seconds=300))
        session.commit()
    assert retention.purge(now=now)['eligible'] == 2
    assert len(factory().query(storage.SecurityLoginAlert).all()) == 3
    first = retention.purge(now=now, dry_run=False, batch_size=1)
    assert first['deleted'] == 1
    assert retention.purge(now=now, dry_run=False)['deleted'] == 1
    assert retention.purge(now=now, dry_run=False)['deleted'] == 0
    assert len(factory().query(storage.SecurityLoginAlert).all()) == 1
    engine.dispose()


@pytest.mark.parametrize('value', ['0', '-1', '3651', 'bad', '2.5'])
def test_invalid_retention(monkeypatch, value):
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_RETENTION_DAYS', value)
    with pytest.raises(ValueError): retention.retention_days()


def test_invalid_purge_arguments():
    with pytest.raises(ValueError): retention.purge(batch_size=0)
    with pytest.raises(ValueError): retention.purge(batch_size=1001)
    with pytest.raises(ValueError): retention.purge(now=datetime(2026, 1, 1))
    with pytest.raises(ValueError): retention.purge(dry_run='false')

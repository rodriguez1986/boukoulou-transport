from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import security_alert_storage_step89 as storage


def test_database_persists_and_filters(monkeypatch, tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "alerts.sqlite"}')
    storage.SecurityLoginAlert.__table__.create(engine)
    monkeypatch.setattr(storage, 'SessionLocal', sessionmaker(bind=engine))
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_STORAGE', 'database')
    assert storage.enabled()
    storage.store({'event': 'login_failure_burst', 'scope': 'user_ref', 'ref': 'hash1', 'count': 10, 'window_seconds': 300, 'password': 'SECRET'})
    storage.store({'event': 'login_failure_burst', 'scope': 'client_ref', 'ref': 'hash2', 'count': 11, 'window_seconds': 300})
    assert [x['id'] for x in storage.recent()] == [2, 1]
    assert [x['id'] for x in storage.recent(scope='user_ref')] == [1]
    assert [x['id'] for x in storage.recent(before_id=2)] == [1]
    assert storage.recent(since=datetime.now(timezone.utc) + timedelta(days=1)) == []
    assert 'SECRET' not in repr(storage.recent())
    engine.dispose()


def test_invalid_alert_and_validation(monkeypatch, tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "alerts2.sqlite"}')
    storage.SecurityLoginAlert.__table__.create(engine)
    monkeypatch.setattr(storage, 'SessionLocal', sessionmaker(bind=engine))
    storage.store({'event': 'unrelated', 'scope': 'user_ref'})
    assert storage.recent() == []
    import pytest
    with pytest.raises(ValueError): storage.recent(scope='invalid')
    with pytest.raises(ValueError): storage.recent(since=datetime(2026, 1, 1))
    engine.dispose()

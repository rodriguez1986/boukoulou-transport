from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import security_alert_purge_history_step92 as history
from app.db import Base

@pytest.fixture
def store(monkeypatch):
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine, tables=[history.SecurityAlertPurgeRun.__table__])
    monkeypatch.setattr(history, 'SessionLocal', sessionmaker(bind=engine))
    yield
    engine.dispose()

def test_history_persistent_order_and_pagination(store):
    first = history.record(status='completed', dry_run=True, batch_size=500, eligible=13)
    second = history.record(status='skipped_locked', dry_run=False, batch_size=100)
    rows = history.recent()
    assert [r['id'] for r in rows] == [second, first]
    assert rows[0]['status'] == 'skipped_locked'
    assert rows[1]['eligible'] == 13
    assert rows[1]['deleted'] == 0
    assert rows[0]['started_at'].endswith('+00:00')
    assert [r['id'] for r in history.recent(limit=1, before_id=second)] == [first]

def test_failure_code_whitelist_and_no_sensitive_fields(store):
    history.record(status='failed', dry_run=False, batch_size=50, error_code='PURGE_FAILED')
    row = history.recent()[0]
    assert row['error_code'] == 'PURGE_FAILED'
    assert set(row) == {'id','started_at','status','dry_run','deleted','eligible','batch_size','error_code'}
    with pytest.raises(ValueError):
        history.record(status='failed', dry_run=False, batch_size=50, error_code='password=secret')

@pytest.mark.parametrize('kwargs', [
    {'status':'unknown', 'dry_run':True, 'batch_size':500},
    {'status':'completed', 'dry_run':1, 'batch_size':500},
    {'status':'completed', 'dry_run':True, 'batch_size':1001},
    {'status':'completed', 'dry_run':True, 'batch_size':500, 'deleted':-1},
])
def test_reject_invalid_record(store, kwargs):
    with pytest.raises(ValueError):
        history.record(**kwargs)

@pytest.mark.parametrize('limit,before_id', [(0,None),(201,None),(True,None),(5,0),(5,True)])
def test_reject_invalid_queries(store, limit, before_id):
    with pytest.raises(ValueError):
        history.recent(limit=limit, before_id=before_id)

def test_endpoint_requires_admin():
    from app.main import app
    from fastapi.routing import APIRoute
    routes = [r for r in app.routes if isinstance(r, APIRoute) and r.path == '/admin/security/purge-runs']
    assert len(routes) == 1
    assert 'GET' in routes[0].methods
    assert any(dep.call.__name__ == 'dep' for dep in routes[0].dependant.dependencies) or routes[0].dependant.dependencies

from datetime import datetime, timedelta, timezone
import pytest
from app import security_alert_registry_step87 as registry


def setup_function():
    registry.reset_for_tests()


def seed():
    for scope in ('user_ref', 'client_ref', 'user_ref', 'client_ref'):
        registry.record({'event': 'login_failure_burst', 'scope': scope, 'ref': 'masked', 'count': 10})


def test_scope_filter_and_order():
    seed()
    assert [a['id'] for a in registry.recent(scope='user_ref')] == [3, 1]
    assert [a['id'] for a in registry.recent(scope='client_ref', limit=1)] == [4]


def test_cursor_combined_with_scope():
    seed()
    assert [a['id'] for a in registry.recent(scope='client_ref', before_id=4)] == [2]
    assert registry.recent(before_id=1) == []


def test_time_filters():
    seed()
    now = datetime.now(timezone.utc)
    assert len(registry.recent(since=now - timedelta(minutes=1), until=now + timedelta(minutes=1))) == 4
    assert registry.recent(since=now + timedelta(minutes=1)) == []
    assert registry.recent(until=now - timedelta(minutes=1)) == []


@pytest.mark.parametrize('kwargs', [
    {'scope': 'unknown'}, {'before_id': 0},
    {'since': datetime(2026, 1, 1)},
    {'until': datetime(2026, 1, 1)},
    {'since': datetime(2026, 1, 2, tzinfo=timezone.utc), 'until': datetime(2026, 1, 1, tzinfo=timezone.utc)},
])
def test_invalid_filters(kwargs):
    with pytest.raises(ValueError):
        registry.recent(**kwargs)


def test_route_filter_contract():
    from app.main import app
    from fastapi.routing import APIRoute
    route = next(r for r in app.routes if isinstance(r, APIRoute) and r.path == '/admin/security/login-alerts')
    names = {p.name for p in route.dependant.query_params}
    assert {'limit', 'scope', 'since', 'until', 'before_id'} <= names
    assert any(d.call is not None for d in route.dependant.dependencies)

from app import security_alert_registry_step87 as registry
from app import login_alert_step86 as detector


def setup_function():
    registry.reset_for_tests()
    detector.reset_for_tests()


def test_detection_creates_consultable_alert():
    for i in range(10):
        detector.observe('login_failed', 'pseudonym', 'network', now=100+i)
    alerts = registry.recent()
    assert len(alerts) == 2
    assert {a['scope'] for a in alerts} == {'user_ref', 'client_ref'}
    assert all(a['event'] == 'login_failure_burst' for a in alerts)
    assert all('occurred_at' in a for a in alerts)


def test_registry_is_bounded_and_sorted():
    for i in range(220):
        registry.record({'event':'login_failure_burst','scope':'client_ref','ref':str(i),'count':10,'password':'secret'})
    result = registry.recent(500)
    assert len(result) == 200
    assert result[0]['ref'] == '219'
    assert result[-1]['ref'] == '20'
    assert all('password' not in row for row in result)


def test_rejects_unexpected_events_and_bounds_limit():
    registry.record({'event':'login_succeeded','scope':'user_ref','ref':'x'})
    registry.record({'event':'login_failure_burst','scope':'unexpected','ref':'x'})
    assert registry.recent() == []
    registry.record({'event':'login_failure_burst','scope':'user_ref','ref':'x'})
    assert len(registry.recent(0)) == 1


def test_admin_route_has_admin_dependency():
    from app.main import app
    from fastapi.routing import APIRoute
    route = next(r for r in app.routes if isinstance(r, APIRoute) and r.path == '/admin/security/login-alerts')
    assert 'GET' in route.methods
    assert any(dependency.call is not None for dependency in route.dependant.dependencies)

import json
import logging
from app import login_alert_step86 as alerts


def setup_function():
    alerts.reset_for_tests()


def test_threshold_and_cooldown(caplog):
    with caplog.at_level(logging.WARNING, logger='boukoulou.security.alert'):
        for i in range(9):
            assert not alerts.observe('login_failed', 'account', now=i)
        assert alerts.observe('login_failed', 'account', now=9)
        assert not alerts.observe('login_failed', 'account', now=10)
        for i in range(600, 609):
            alerts.observe('login_failed', 'account', now=i)
        assert alerts.observe('login_failed', 'account', now=609)
    messages = [json.loads(r.message) for r in caplog.records if r.name == 'boukoulou.security.alert']
    assert len(messages) == 2
    assert all(m['scope'] == 'user_ref' for m in messages)


def test_ip_across_multiple_accounts():
    for i in range(9):
        assert not alerts.observe('login_failed', f'user{i}', 'same-ip', now=i)
    assert alerts.observe('login_failed', 'user9', 'same-ip', now=9)


def test_no_raw_identifiers_when_refs_missing(caplog):
    with caplog.at_level(logging.WARNING, logger='boukoulou.security.alert'):
        for i in range(20):
            assert not alerts.observe('login_failed', now=i)
    assert not [r for r in caplog.records if r.name == 'boukoulou.security.alert']


def test_success_does_not_count():
    for i in range(20):
        assert not alerts.observe('login_succeeded', 'account', 'ip', now=i)
    assert not alerts.observe('login_failed', 'account', 'ip', now=20)


def test_window_expiry():
    for i in range(9):
        alerts.observe('login_failed', 'account', now=i)
    assert not alerts.observe('login_failed', 'account', now=500)


def test_bounded_cardinality():
    original = alerts.MAX_KEYS
    alerts.MAX_KEYS = 5
    try:
        for i in range(20):
            alerts.observe('login_failed', f'account{i}', now=i)
        assert len(alerts._events) <= 5
    finally:
        alerts.MAX_KEYS = original

import json
import logging
from types import SimpleNamespace
import pytest
from app import login_audit_step85 as audit


def test_log_without_key_does_not_disclose_identity(monkeypatch, caplog):
    monkeypatch.delenv('BOUKOULOU_LOGIN_AUDIT_KEY', raising=False)
    req = SimpleNamespace(client=SimpleNamespace(host='192.0.2.21'), headers={})
    with caplog.at_level(logging.WARNING, logger='boukoulou.security.login'):
        audit.emit('login_failed', 'SecretUser', req, 'invalid_credentials')
    record = json.loads(caplog.records[-1].message)
    assert record == {'component': 'auth.login', 'event': 'login_failed', 'reason': 'invalid_credentials'}
    assert 'SecretUser' not in caplog.text and '192.0.2.21' not in caplog.text


def test_keyed_references_stable_and_private(monkeypatch, caplog):
    monkeypatch.setenv('BOUKOULOU_LOGIN_AUDIT_KEY', 'dedicated-test-key')
    req = SimpleNamespace(client=SimpleNamespace(host='192.0.2.21'), headers={})
    with caplog.at_level(logging.WARNING, logger='boukoulou.security.login'):
        audit.emit('login_blocked', 'SecretUser', req, 'ip_limit')
        audit.emit('login_blocked', ' secretuser ', req, 'ip_limit')
    a,b = [json.loads(r.message) for r in caplog.records[-2:]]
    assert a == b and len(a['user_ref']) == 24 and len(a['client_ref']) == 24
    assert 'SecretUser' not in caplog.text and '192.0.2.21' not in caplog.text


def test_reject_unknown_events():
    with pytest.raises(ValueError):
        audit.emit('password_dump')


def test_unknown_reason_not_logged(caplog):
    with caplog.at_level(logging.WARNING, logger='boukoulou.security.login'):
        audit.emit('login_succeeded', reason='raw-password')
    assert 'raw-password' not in caplog.text

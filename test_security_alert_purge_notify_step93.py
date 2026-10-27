import pytest
from app import security_alert_purge_notify_step93 as notify


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', raising=False)
    assert notify.notify_failure() == 'disabled'


def test_enabled_requires_configuration(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', 'enabled')
    for key in ('BOUKOULOU_PURGE_SMTP_HOST', 'BOUKOULOU_PURGE_SMTP_FROM', 'BOUKOULOU_PURGE_SMTP_TO'):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(ValueError):
        notify.notify_failure()


def test_rejects_unapproved_error_code(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', 'enabled')
    with pytest.raises(ValueError):
        notify.notify_failure(error_code='secret')


def test_sends_redacted_email(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', 'enabled')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_HOST', 'smtp.example.org')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_FROM', 'alerts@example.org')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_TO', 'admin@example.org')
    monkeypatch.delenv('BOUKOULOU_PURGE_SMTP_USER', raising=False)
    monkeypatch.delenv('BOUKOULOU_PURGE_SMTP_PASSWORD', raising=False)
    sent = []
    class FakeSMTP:
        def __init__(self, host, port, timeout, context):
            assert (host, port, timeout) == ('smtp.example.org', 465, 10)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def send_message(self, message): sent.append(message)
    monkeypatch.setattr(notify.smtplib, 'SMTP_SSL', FakeSMTP)
    assert notify.notify_failure() == 'sent'
    assert len(sent) == 1
    assert 'PURGE_FAILED' in sent[0].get_content()
    assert sent[0]['To'] == 'admin@example.org'


def test_rejects_header_injection(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_PURGE_FAILURE_NOTIFY', 'enabled')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_HOST', 'smtp.example.org')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_FROM', 'alerts@example.org')
    monkeypatch.setenv('BOUKOULOU_PURGE_SMTP_TO', 'admin@example.org\nBcc:evil@example.org')
    with pytest.raises(ValueError):
        notify.notify_failure()

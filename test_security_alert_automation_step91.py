import pytest
from app import security_alert_automation_step91 as auto
from scripts import purge_security_alerts_step91 as cli


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('BOUKOULOU_SECURITY_ALERT_AUTO_PURGE', raising=False)
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_STORAGE', 'database')
    with pytest.raises(ValueError, match='non activée'):
        auto.run_scheduled()


def test_requires_sql_storage(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_AUTO_PURGE', 'enabled')
    monkeypatch.delenv('BOUKOULOU_SECURITY_ALERT_STORAGE', raising=False)
    with pytest.raises(ValueError, match='Stockage SQL'):
        auto.run_scheduled()


@pytest.mark.parametrize('batch', [0, 1001, True, '500'])
def test_batch_guard(monkeypatch, batch):
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_AUTO_PURGE', 'enabled')
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_STORAGE', 'database')
    with pytest.raises(ValueError):
        auto.run_scheduled(batch_size=batch)


def test_requires_postgres(monkeypatch, tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_AUTO_PURGE', 'enabled')
    monkeypatch.setenv('BOUKOULOU_SECURITY_ALERT_STORAGE', 'database')
    engine = create_engine(f'sqlite:///{tmp_path / "a.db"}')
    monkeypatch.setattr(auto.retention, 'SessionLocal', sessionmaker(bind=engine))
    with pytest.raises(ValueError, match='PostgreSQL'):
        auto.run_scheduled()
    engine.dispose()


def test_cli_fail_closed(monkeypatch, capsys):
    def deny(**kwargs):
        raise ValueError('refus')
    monkeypatch.setattr(cli, 'run_scheduled', deny)
    assert cli.main(['--apply']) == 1
    assert 'ValueError' in capsys.readouterr().err


def test_cli_dry_run_by_default(monkeypatch, capsys):
    seen = []
    monkeypatch.setattr(cli, 'run_scheduled', lambda **kwargs: (seen.append(kwargs) or {'status': 'completed', 'deleted': 0}))
    assert cli.main([]) == 0
    assert seen == [{'apply': False, 'batch_size': 500}]
    assert 'completed' in capsys.readouterr().out

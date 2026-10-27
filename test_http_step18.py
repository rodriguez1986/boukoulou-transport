"""Vérifications statiques des protections du smoke HTTP de l'étape 18."""
import ast
from pathlib import Path

ROOT = Path(__file__).parent
SCRIPT = (ROOT / 'scripts' / 'smoke_http_etape18.py').read_text(encoding='utf-8')

def test_smoke_syntax():
    ast.parse(SCRIPT)

def test_sqlite_memory_only():
    assert "sqlite:///:memory:" in SCRIPT
    assert "BOUKOULOU_ENABLE_DEV_SEED'] = '0'" in SCRIPT

def test_http_endpoints_and_status():
    for endpoint in ('/health', '/auth/me', '/cash/sessions/open'):
        assert endpoint in SCRIPT
    assert 'health.status_code == 200' in SCRIPT
    assert 'me.status_code == 401' in SCRIPT
    assert 'cash.status_code == 401' in SCRIPT

def test_no_migration_or_postgres():
    assert 'create_all(' not in SCRIPT
    assert 'alembic' not in SCRIPT
    assert 'postgresql://' not in SCRIPT

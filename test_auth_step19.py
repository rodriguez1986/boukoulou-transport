"""Contrôles statiques des scénarios HTTP isolés."""
import ast
from pathlib import Path
ROOT=Path(__file__).parent
SCRIPT=(ROOT/'scripts'/'smoke_auth_etape19.py').read_text(encoding='utf-8')

def test_script_syntax():
    ast.parse(SCRIPT)

def test_no_db_write():
    assert "sqlite:///:memory:" in SCRIPT
    assert 'app.dependency_overrides[get_db] = fake_db' in SCRIPT
    assert 'create_all(' not in SCRIPT
    assert 'alembic' not in SCRIPT

def test_expected_scenarios():
    for phrase in ('JWT valide','DRIVER caisse','version révoquée','JWT expiré',
                   'utilisateur désactivé','utilisateur absent'):
        assert phrase in SCRIPT

def test_cleanup_override():
    assert 'finally:' in SCRIPT
    assert 'app.dependency_overrides.pop(get_db,None)' in SCRIPT

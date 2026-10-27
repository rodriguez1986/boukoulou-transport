"""Tests de garde-fous avant import de l'application (sans base de données)."""
import ast
from pathlib import Path

ROOT = Path(__file__).parent
SRC = (ROOT/'app'/'main.py').read_text(encoding='utf-8-sig')
TREE = ast.parse(SRC)

def test_pas_de_creation_automatique_tables():
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == 'create_all' for n in ast.walk(TREE))

def test_seed_desactive_par_defaut():
    assert 'BOUKOULOU_ENABLE_DEV_SEED' in SRC
    assert 'if os.getenv("BOUKOULOU_ENABLE_DEV_SEED") != "1":' in SRC

def test_import_isole_sqlite_memoire():
    smoke = (ROOT/'scripts'/'smoke_import_etape16.py').read_text()
    assert 'sqlite:///:memory:' in smoke
    assert 'BOUKOULOU_ENABLE_DEV_SEED' in smoke
    assert 'from app.main import app' in smoke

def test_script_powershell_ne_demarre_pas_docker():
    script = (ROOT/'scripts'/'tester_import_etape17.ps1').read_text().lower()
    assert 'docker compose' not in script
    assert 'alembic upgrade' not in script
    assert 'diagnostic_import_etape17.py' in script

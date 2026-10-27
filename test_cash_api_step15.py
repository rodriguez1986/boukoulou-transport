"""Tests de contrat du backend, sans DB ni import de l'application."""
import ast
from pathlib import Path

ROOT=Path(__file__).parent
SOURCE=(ROOT/"app"/"main.py").read_text(encoding="utf-8-sig")
TREE=ast.parse(SOURCE)

def get_route(method,path):
    for n in TREE.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for d in n.decorator_list:
                if (isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute)
                    and d.func.attr==method and d.args
                    and isinstance(d.args[0],ast.Constant) and d.args[0].value==path):
                    return n
    raise AssertionError(f"Route absente : {method.upper()} {path}")

def test_open_exige_authentification_et_roles():
    n=get_route("post","/cash/sessions/open")
    dependencies=[ast.unparse(d) for d in n.args.defaults]
    assert any("Depends(roles(" in d and all(r in d for r in ("ADMIN","AGENT","CONTROLLER")) for d in dependencies)

def test_http_409_si_caisse_ouverte():
    code=ast.get_source_segment(SOURCE,get_route("post","/cash/sessions/open"))
    assert code.count("status_code=409")>=2
    assert "CASH_ALREADY_OPEN" in code

def test_contrainte_unique_avec_rollback():
    code=ast.get_source_segment(SOURCE,get_route("post","/cash/sessions/open"))
    assert "except IntegrityError as exc:" in code
    assert "db.rollback()" in code
    assert 'constraint == "ux_cash_sessions_one_open_per_user"' in code

def test_pas_de_migration_dans_script_diagnostic():
    code=(ROOT/"scripts"/"diagnostic_etape15.py").read_text(encoding="utf-8")
    assert "importlib.util.find_spec" in code
    assert "create_all(" not in code
    assert "subprocess" not in code

def test_index_postgresql_prepare():
    sql=(ROOT/"migrations"/"v59_one_open_cash_session_step10.sql").read_text()
    assert "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS" in sql
    assert "WHERE status = 'OPEN'" in sql

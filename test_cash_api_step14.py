"""Vérifications supplémentaires sans PostgreSQL; tests HTTP conditionnels."""
import ast
from pathlib import Path
import pytest

SRC = (Path(__file__).parent/"app"/"main.py").read_text(encoding="utf-8-sig")
TREE = ast.parse(SRC)

def cash_open():
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if (isinstance(decorator, ast.Call) and
                    isinstance(decorator.func, ast.Attribute) and
                    decorator.func.attr == "post" and decorator.args and
                    isinstance(decorator.args[0], ast.Constant) and
                    decorator.args[0].value == "/cash/sessions/open"):
                    return node
    raise AssertionError("Route d'ouverture de caisse absente")

def test_index_conflit_reconnu_par_nom():
    code = ast.get_source_segment(SRC, cash_open())
    assert 'constraint == "ux_cash_sessions_one_open_per_user"' in code
    assert "except IntegrityError as exc:" in code

def test_transaction_annulee_avant_reponse():
    code = ast.get_source_segment(SRC, cash_open())
    rollback = code.index("db.rollback()")
    conflict = code.index('if constraint == "ux_cash_sessions_one_open_per_user"')
    assert rollback < conflict

def test_pas_de_migration_automatique_dans_script_test():
    script = (Path(__file__).parent/"scripts"/"tester_http_etape14.ps1").read_text()
    assert "pytest" in script and "requirements.txt" in script
    assert "docker compose up" not in script.lower()
    assert "alembic upgrade" not in script.lower()

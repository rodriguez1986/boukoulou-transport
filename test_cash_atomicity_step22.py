"""Contrôles du contrat transactionnel, sans base PostgreSQL."""
import ast
from pathlib import Path

ROOT = Path(__file__).parent
SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8-sig")
TREE = ast.parse(SOURCE)

def close_function():
    for node in TREE.body:
        if isinstance(node, ast.FunctionDef) and node.name == "close_cash_session":
            return node
    raise AssertionError("Route de clôture absente")

def test_audit_ajoute_avant_commit():
    code = ast.get_source_segment(SOURCE, close_function())
    assert 'action="CLOSE_CASH_SESSION"' in code
    assert code.index('db.add(Audit(') < code.index('db.commit()')

def test_une_seule_validation_de_transaction():
    node = close_function()
    commits = [n for n in ast.walk(node) if isinstance(n, ast.Call)
               and isinstance(n.func, ast.Attribute) and n.func.attr == 'commit']
    assert len(commits) == 1

def test_rollback_si_echec():
    node = close_function()
    handlers = [h for n in ast.walk(node) if isinstance(n, ast.Try) for h in n.handlers]
    assert any(any(isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)
                       and x.func.attr == 'rollback' for x in ast.walk(h))
               and any(isinstance(x, ast.Raise) for x in ast.walk(h)) for h in handlers)

def test_pas_de_double_audit_apres_commit():
    code = ast.get_source_segment(SOURCE, close_function())
    assert 'audit(db, user, "CLOSE_CASH_SESSION"' not in code

def test_montant_attendu_limite_aux_especes():
    code = ast.get_source_segment(SOURCE, close_function())
    assert 'expected = session.opening_amount + cash_revenue' in code
    assert 'session.difference_amount = data.declared_amount - expected' in code

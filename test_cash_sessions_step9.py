"""Contrôles structurels de sécurité des caisses (sans DB)."""
import ast
from pathlib import Path

SRC = (Path(__file__).parent / 'app' / 'main.py').read_text(encoding='utf-8')
TREE = ast.parse(SRC)
FUNCS = {n.name: n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

def source(name):
    return ast.get_source_segment(SRC, FUNCS[name])

def role_dependency(name):
    n = FUNCS[name]
    for default in [*n.args.defaults, *(d for d in n.args.kw_defaults if d)]:
        if isinstance(default, ast.Call) and isinstance(default.func, ast.Name) and default.func.id == 'Depends':
            inner = default.args[0]
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == 'roles':
                return {a.value for a in inner.args if isinstance(a, ast.Constant)}
    return None

def test_open_current_close_authenticated():
    for name in ('open_cash_session', 'current_cash_session', 'close_cash_session'):
        assert role_dependency(name) == {'ADMIN', 'AGENT', 'CONTROLLER'}

def test_current_session_is_own_only():
    assert 'CashSession.user_id == user.id' in source('current_cash_session')
    assert 'CashSession.status == "OPEN"' in source('current_cash_session')

def test_open_prevents_second_open_session():
    s = source('open_cash_session')
    assert 'CashSession.user_id == user.id' in s
    assert 'CashSession.status == "OPEN"' in s
    assert 'status_code=409' in s

def test_close_prevents_other_users_except_admin():
    s = source('close_cash_session')
    assert 'session.user_id != user.id and role_value != "ADMIN"' in s
    assert 'status_code=403' in s
    assert 'session.status != "OPEN"' in s

def test_rectification_and_history_admin_only():
    for name in ('rectify_cash_session', 'list_cash_rectifications'):
        assert role_dependency(name) == {'ADMIN'}

def test_rectification_closed_and_audited():
    s = source('rectify_cash_session')
    assert 'with_for_update()' in s
    assert 'session.status != "CLOSED"' in s
    assert 'RECTIFY_CASH_SESSION' in s
    assert 'db.rollback()' in s

def test_close_uses_cash_only_for_expected_amount():
    s = source('close_cash_session')
    assert 'recettes_par_provider.get("CASH", 0)' in s
    assert 'expected = session.opening_amount + cash_revenue' in s

"""Tests statiques sans base, réseau ou dépendance externe."""
import ast
from pathlib import Path

SOURCE = (Path(__file__).parent / 'app' / 'main.py').read_text(encoding='utf-8')
TREE = ast.parse(SOURCE)
ROUTES = {}
for node in TREE.body:
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr in ('get','post') and dec.args and isinstance(dec.args[0], ast.Constant):
                ROUTES[(dec.func.attr.upper(), dec.args[0].value)] = node

def _defaults(node):
    return ' '.join(ast.unparse(x) for x in node.args.defaults + [x for x in node.args.kw_defaults if x is not None])

def test_caisse_authentification_et_roles():
    expected = {
        ('POST','/cash/sessions/open'): ('ADMIN','AGENT','CONTROLLER'),
        ('GET','/cash/sessions/current'): ('ADMIN','AGENT','CONTROLLER'),
        ('POST','/cash/sessions/{session_id}/close'): ('ADMIN','AGENT','CONTROLLER'),
        ('POST','/cash/sessions/{session_id}/rectify'): ('ADMIN',),
        ('GET','/cash/sessions/{session_id}/rectifications'): ('ADMIN',),
        ('GET','/admin/dashboard/cash/sessions'): ('ADMIN',),
    }
    for route, roles in expected.items():
        assert route in ROUTES, f'Route manquante: {route}'
        actual = _defaults(ROUTES[route])
        assert 'Depends(roles(' in actual, f'Authentification absente: {route}'
        for role in roles:
            assert repr(role) in actual or '"'+role+'"' in actual, (route,role)

def test_fermeture_caisse_controle_proprietaire():
    code = ast.get_source_segment(SOURCE, ROUTES[('POST','/cash/sessions/{session_id}/close')])
    assert 'session.user_id != user.id' in code
    assert 'role_value != "ADMIN"' in code

def test_caisse_courante_limitee_utilisateur():
    code = ast.get_source_segment(SOURCE, ROUTES[('GET','/cash/sessions/current')])
    assert 'CashSession.user_id == user.id' in code

def test_rectification_admin_et_verrouillage():
    code = ast.get_source_segment(SOURCE, ROUTES[('POST','/cash/sessions/{session_id}/rectify')])
    assert '.with_for_update()' in code
    assert 'session.status != "CLOSED"' in code

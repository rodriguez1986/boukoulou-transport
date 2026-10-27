"""Audit statique des permissions de caisse. Aucun accès DB ou HTTP."""
import ast
from pathlib import Path

SRC=(Path(__file__).parent/'app'/'main.py').read_text(encoding='utf-8-sig')
TREE=ast.parse(SRC)

def route(method,path):
    for node in TREE.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if (isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute)
                    and dec.func.attr==method and dec.args
                    and isinstance(dec.args[0],ast.Constant) and dec.args[0].value==path):
                    return node
    raise AssertionError(f'Route absente : {method} {path}')

def roles_for(method,path):
    node=route(method,path)
    defaults=node.args.defaults+[x for x in node.args.kw_defaults if x is not None]
    role_deps=[]
    for value in defaults:
        if (isinstance(value,ast.Call) and isinstance(value.func,ast.Name)
            and value.func.id=='Depends' and value.args):
            inner=value.args[0]
            if isinstance(inner,ast.Call) and isinstance(inner.func,ast.Name) and inner.func.id=='roles':
                role_deps.append(tuple(x.value for x in inner.args if isinstance(x,ast.Constant)))
    assert len(role_deps)==1, f'Dépendance de rôles ambiguë : {path}'
    return set(role_deps[0])

def body(method,path):
    return ast.get_source_segment(SRC,route(method,path))

def test_ouverture_et_consultation_reservees_aux_trois_roles():
    allowed={'ADMIN','AGENT','CONTROLLER'}
    assert roles_for('post','/cash/sessions/open')==allowed
    assert roles_for('get','/cash/sessions/current')==allowed
    assert 'CashSession.user_id == user.id' in body('get','/cash/sessions/current')

def test_cloture_et_propriete():
    assert roles_for('post','/cash/sessions/{session_id}/close')=={'ADMIN','AGENT','CONTROLLER'}
    code=body('post','/cash/sessions/{session_id}/close')
    assert 'session.user_id != user.id and role_value != "ADMIN"' in code
    assert 'status_code=403' in code
    assert 'session.status != "OPEN"' in code

def test_rectification_admin_uniquement():
    path='/cash/sessions/{session_id}/rectify'
    assert roles_for('post',path)=={'ADMIN'}
    code=body('post',path)
    assert '.with_for_update()' in code
    assert 'session.status != "CLOSED"' in code

def test_historique_et_dashboard_admin_uniquement():
    for method,path in [('get','/cash/sessions/{session_id}/rectifications'),
                        ('get','/admin/dashboard/cash/sessions'),
                        ('get','/admin/dashboard/cash/sessions/export.xlsx'),
                        ('get','/admin/cash/sessions/{session_id}/report.pdf')]:
        assert roles_for(method,path)=={'ADMIN'}

def test_aucun_driver_autorise_sur_routes_caisse():
    paths=[('post','/cash/sessions/open'),('get','/cash/sessions/current'),
           ('post','/cash/sessions/{session_id}/close'),
           ('post','/cash/sessions/{session_id}/rectify'),
           ('get','/cash/sessions/{session_id}/rectifications'),
           ('get','/admin/dashboard/cash/sessions')]
    assert all('DRIVER' not in roles_for(method,path) for method,path in paths)

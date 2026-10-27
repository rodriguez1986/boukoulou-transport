"""Contrôles statiques des restrictions des routes financières (sans DB)."""
import ast
from pathlib import Path

ROOT = Path(__file__).parent / 'app'

def endpoints(filename):
    tree = ast.parse((ROOT / filename).read_text(encoding='utf-8'))
    result = {}
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.args:
                if isinstance(decorator.args[0], ast.Constant):
                    result[(decorator.func.attr, decorator.args[0].value)] = node
    return result

def allowed_roles(node):
    deps = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
    for d in deps:
        if isinstance(d, ast.Call) and isinstance(d.func, ast.Name) and d.func.id == 'Depends' and d.args:
            inner = d.args[0]
            if isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name) and inner.func.id == 'roles':
                return {arg.value for arg in inner.args if isinstance(arg, ast.Constant)}
    return None

def test_admin_only_finance_routers():
    for name, path in [('finance_dashboard.py', '/summary'), ('finance_audit.py', '/cash-anomalies')]:
        assert allowed_roles(endpoints(name)[('get', path)]) == {'ADMIN'}

def test_admin_only_finance_exports():
    routes = endpoints('main.py')
    for path in ('/admin/dashboard/cash', '/admin/dashboard/cash/sessions',
                 '/admin/dashboard/cash/sessions/export.xlsx',
                 '/admin/cash/sessions/{session_id}/report.pdf'):
        assert allowed_roles(routes[('get', path)]) == {'ADMIN'}, path

def test_cash_daily_restricted_to_admin_or_agent():
    routes = endpoints('main.py')
    for path in ('/cash/daily', '/cash/daily/details', '/cash/by-line', '/cash/by-trip'):
        assert allowed_roles(routes[('get', path)]) == {'ADMIN', 'AGENT'}, path

def test_finance_routes_do_not_expose_country_manager():
    for filename in ('main.py', 'finance_dashboard.py', 'finance_audit.py'):
        for (method, path), node in endpoints(filename).items():
            if path.startswith(('/finance', '/cash', '/admin/dashboard/cash', '/admin/cash')):
                assert allowed_roles(node) is not None, (filename, method, path)

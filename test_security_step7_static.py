"""Contrôles statiques sans connexion PostgreSQL."""
import ast
from pathlib import Path
src=(Path(__file__).parent/'app/main.py').read_text()
tree=ast.parse(src)
routes={}
for node in tree.body:
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
        for d in node.decorator_list:
            if isinstance(d,ast.Call) and isinstance(d.func,ast.Attribute) and d.func.attr=='get' and d.args and isinstance(d.args[0],ast.Constant):
                routes[d.args[0].value]=node

def test_reseau_sans_acces_anonyme():
    for path in ('/countries','/lines','/vehicles','/trips'):
        defaults=[ast.unparse(x) for x in routes[path].args.defaults]
        assert any('Depends(roles(' in x for x in defaults),path
        assert all('utilisateur_optionnel' not in x for x in defaults),path

def test_filtrage_pays():
    s=ast.get_source_segment(src,routes['/countries'])
    assert 'u.role.value == "COUNTRY_MANAGER"' in s
    assert 'Country.id == u.country_id' in s

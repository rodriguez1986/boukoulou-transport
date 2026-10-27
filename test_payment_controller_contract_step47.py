import ast
from pathlib import Path

def test_driver_et_controleur_meme_role_bus():
    tree = ast.parse((Path(__file__).parent / 'app' / 'payment_api_step45.py').read_text())
    mapping = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == '_ROLE_MAP' for t in n.targets))
    roles = {k.value: v.id for k, v in zip(mapping.keys, mapping.values)}
    assert roles['DRIVER'] == roles['CONTROLLER'] == 'AGENT_BUS'
    assert 'ADMIN' not in roles

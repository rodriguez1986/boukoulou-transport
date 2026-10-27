"""Régressions statiques de sécurité au démarrage."""
import ast
from pathlib import Path
SRC=(Path(__file__).parent/"app"/"main.py").read_text(encoding="utf-8-sig")
TREE=ast.parse(SRC)

def test_aucun_create_all_automatique():
    assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="create_all" for n in ast.walk(TREE))

def test_seed_desactive_par_defaut():
    fn=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=="seed")
    assert isinstance(fn.body[0],ast.If)
    assert 'BOUKOULOU_ENABLE_DEV_SEED' in ast.unparse(fn.body[0].test)
    assert isinstance(fn.body[0].body[0],ast.Return)

def test_script_import_avec_base_memoire():
    src=(Path(__file__).parent/"scripts"/"smoke_import_etape16.py").read_text()
    assert 'sqlite:///:memory:' in src
    assert 'BOUKOULOU_ENABLE_DEV_SEED' in src
    assert 'from app.main import app' in src

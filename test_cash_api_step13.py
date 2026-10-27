"""Tests API des caisses : contrôles statiques et HTTP simulés sans PostgreSQL."""
import ast
from pathlib import Path
import pytest

ROOT=Path(__file__).parent
SRC=(ROOT/"app"/"main.py").read_text(encoding="utf-8-sig")
TREE=ast.parse(SRC)

def route(path, method):
    for node in TREE.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute):
                    if dec.func.attr==method and dec.args and isinstance(dec.args[0],ast.Constant) and dec.args[0].value==path:
                        return node
    raise AssertionError(f"Route absente : {method.upper()} {path}")

def test_routes_caisse_definies():
    assert route("/cash/sessions/open","post")
    assert route("/cash/sessions/current","get")
    assert route("/cash/sessions/{session_id}/close","post")
    assert route("/cash/sessions/{session_id}/rectify","post")

def test_ouverture_controle_roles_et_conflit():
    node=route("/cash/sessions/open","post")
    defaults=[ast.unparse(x) for x in node.args.defaults]
    assert any('roles(' in d and all(role in d for role in ("ADMIN","AGENT","CONTROLLER")) for d in defaults)
    code=ast.get_source_segment(SRC,node)
    assert "CASH_ALREADY_OPEN" in code and "status_code=409" in code
    assert "db.rollback()" in code
    assert "ux_cash_sessions_one_open_per_user" in code

def test_cloture_verifie_proprietaire():
    code=ast.get_source_segment(SRC,route("/cash/sessions/{session_id}/close","post"))
    assert "session.user_id != user.id" in code
    assert 'role_value != "ADMIN"' in code
    assert "status_code=403" in code

def test_rectification_admin_uniquement():
    node=route("/cash/sessions/{session_id}/rectify","post")
    assert any('roles(\'ADMIN\')' in ast.unparse(x) or 'roles("ADMIN")' in ast.unparse(x) for x in node.args.defaults)

@pytest.fixture
def http_app():
    pytest.importorskip("fastapi")
    pytest.importorskip("sqlalchemy")
    pytest.importorskip("passlib")
    pytest.importorskip("jwt")
    pytest.importorskip("reportlab")
    pytest.importorskip("openpyxl")
    pytest.importorskip("qrcode")
    from fastapi.testclient import TestClient
    from app import main, security
    from app.db import get_db
    from types import SimpleNamespace
    class FakeQuery:
        def filter(self,*args,**kwargs): return self
        def first(self): return object()
    class FakeDb:
        def query(self,*args): return FakeQuery()
    main.app.dependency_overrides[get_db]=lambda: FakeDb()
    main.app.dependency_overrides[security.user]=lambda: SimpleNamespace(id=7,username="test",role=SimpleNamespace(value="AGENT"))
    try:
        with TestClient(main.app) as client:
            yield client
    finally:
        main.app.dependency_overrides.clear()

def test_http_409_caisse_deja_ouverte(http_app):
    response=http_app.post("/cash/sessions/open",json={"opening_amount":1000,"notes":"test"})
    assert response.status_code==409, response.text
    assert response.json()["detail"]["code"]=="CASH_ALREADY_OPEN"

def test_http_403_role_interdit(http_app):
    from app import main, security
    from types import SimpleNamespace
    main.app.dependency_overrides[security.user]=lambda: SimpleNamespace(id=8,username="non_autorise",role=SimpleNamespace(value="DRIVER"))
    response=http_app.post("/cash/sessions/open",json={"opening_amount":1000,"notes":"test"})
    assert response.status_code==403, response.text

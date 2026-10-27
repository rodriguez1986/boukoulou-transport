"""Étape 65 : démarrage FastAPI lifespan, seed explicite et absence d'événements dépréciés."""
import ast
from pathlib import Path

from fastapi.testclient import TestClient

from app import main


def test_lifespan_est_configure_sans_on_event():
    source = (Path(__file__).parent / 'app' / 'main.py').read_text(encoding='utf-8')
    tree = ast.parse(source)
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                   and n.func.attr == 'on_event' for n in ast.walk(tree))
    assert any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "FastAPI"
               and any(kw.arg == "lifespan" and isinstance(kw.value, ast.Name)
                       and kw.value.id == "lifespan" for kw in n.keywords)
               for n in ast.walk(tree))


def test_lifespan_appelle_seed_une_fois_par_cycle(monkeypatch):
    calls = []
    monkeypatch.setattr(main, 'seed', lambda: calls.append('startup'))
    with TestClient(main.app) as client:
        assert calls == ['startup']
        assert client.get('/health').json() == {'status': 'ok'}
    assert calls == ['startup']


def test_seed_desactive_par_defaut_sans_connexion_bdd(monkeypatch):
    monkeypatch.delenv('BOUKOULOU_ENABLE_DEV_SEED', raising=False)
    def forbidden_session():
        raise AssertionError('Ne pas ouvrir de connexion DB quand le seed est désactivé')
    monkeypatch.setattr(main, 'SessionLocal', forbidden_session)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200


def test_seed_dev_ferme_session(monkeypatch):
    monkeypatch.setenv('BOUKOULOU_ENV', 'development')
    monkeypatch.setenv('BOUKOULOU_ENABLE_DEV_SEED', '1')
    class FakeQuery:
        def filter_by(self, **kwargs): return self
        def first(self): return object()
    class FakeSession:
        closed = False
        committed = False
        def query(self, model): return FakeQuery()
        def commit(self): self.committed = True
        def close(self): self.closed = True
    db = FakeSession()
    monkeypatch.setattr(main, 'SessionLocal', lambda: db)
    with TestClient(main.app) as client:
        assert client.get('/health').status_code == 200
    assert db.committed and db.closed

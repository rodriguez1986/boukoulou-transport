"""Tests dynamiques isolés du corps réel de clôture, sans DB ni réseau.

Ils n'évaluent pas les décorateurs FastAPI et ne remplacent pas PostgreSQL.
"""
import ast
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest

SOURCE = (Path(__file__).parent / 'app' / 'main.py').read_text(encoding='utf-8-sig')
TREE = ast.parse(SOURCE)
NODE = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'close_cash_session')

class FakeColumn:
    def __eq__(self, other): return self
    def __add__(self, other): return self

class FakeModel:
    id = FakeColumn()
    cash_session_id = FakeColumn()
    status = FakeColumn()
    amount = FakeColumn()
    total_amount = FakeColumn()

class FakeQuery:
    def __init__(self, value): self.value = value
    def filter(self, *args): return self
    def with_for_update(self, *args, **kwargs): return self
    def first(self): return self.value
    def scalar(self): return 0

class FakeDB:
    def __init__(self, session, *, fail_add=False, fail_commit=False):
        self.session = session
        self.fail_add = fail_add
        self.fail_commit = fail_commit
        self.add_calls = self.commit_calls = self.rollback_calls = self.refresh_calls = 0
    def query(self, *args):
        if args and args[0] is FakeModel: return FakeQuery(self.session)
        return FakeQuery(None)
    def add(self, obj):
        self.add_calls += 1
        if self.fail_add: raise RuntimeError('audit indisponible')
    def commit(self):
        self.commit_calls += 1
        if self.fail_commit: raise RuntimeError('commit impossible')
    def rollback(self): self.rollback_calls += 1
    def refresh(self, obj): self.refresh_calls += 1

class FakeHTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail

class FakeFunc:
    @staticmethod
    def sum(x): return 0
    @staticmethod
    def coalesce(*args): return 0

class FakePaymentStatus:
    SUCCESS = 'SUCCESS'

class FakeAudit:
    def __init__(self, **kwargs): self.kwargs = kwargs

# Compile uniquement la fonction extraite du vrai app/main.py.
# Les annotations et valeurs par défaut sont neutralisées pour ne pas importer l'app.
function = ast.FunctionDef(name=NODE.name, args=NODE.args, body=NODE.body,
                           decorator_list=[], returns=None, type_comment=None)
function.args.defaults = []
function.args.kw_defaults = [None for _ in function.args.kwonlyargs]
for arg in [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]:
    arg.annotation = None
ast.fix_missing_locations(function)
module = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
namespace = {
    'CashSession': FakeModel, 'Payment': FakeModel, 'OnboardSale59': FakeModel,
    'PaymentStatus': FakePaymentStatus, 'func': FakeFunc(), 'Audit': FakeAudit,
    'HTTPException': FakeHTTPException, 'datetime': datetime, 'timezone': timezone,
    'calculate_agency_revenue': lambda *a, **kw: 0,
    'calculer_recettes_par_provider': lambda *a, **kw: {'CASH': 75, 'CARD': 25},
}
exec(compile(module, 'app/main.py (fonction isolée)', 'exec'), namespace)
close_cash = namespace['close_cash_session']

def make_session(**overrides):
    data = dict(id=7, user_id=2, status='OPEN', opening_amount=100,
                opened_at=None, notes=None)
    data.update(overrides)
    return SimpleNamespace(**data)

def make_user(**overrides):
    data = dict(id=2, username='agent-test', role='AGENT')
    data.update(overrides)
    return SimpleNamespace(**data)

def test_montants_et_validation_unique():
    s = make_session(); db = FakeDB(s)
    result = close_cash(7, SimpleNamespace(declared_amount=180, notes='OK'), db, make_user())
    assert result['expected_amount'] == 175
    assert result['difference_amount'] == 5
    assert result['sales_revenue'] == 100
    assert result['status'] == 'CLOSED'
    assert db.add_calls == db.commit_calls == db.refresh_calls == 1
    assert db.rollback_calls == 0

@pytest.mark.parametrize('failure', ['fail_add', 'fail_commit'])
def test_echec_audit_ou_commit_entraine_rollback(failure):
    s = make_session(); db = FakeDB(s, **{failure: True})
    with pytest.raises(RuntimeError):
        close_cash(7, SimpleNamespace(declared_amount=180, notes=None), db, make_user())
    assert db.rollback_calls == 1
    assert db.refresh_calls == 0
    # Dans un vrai SQLAlchemy Session, rollback restaure l'état persistant.
    # Le FakeDB ne simule pas la restauration des attributs Python.

def test_refus_autre_agent_sans_ecriture():
    db = FakeDB(make_session(user_id=3))
    with pytest.raises(FakeHTTPException) as exc:
        close_cash(7, SimpleNamespace(declared_amount=0, notes=None), db, make_user())
    assert exc.value.status_code == 403
    assert db.add_calls == db.commit_calls == 0

def test_refus_deja_fermee_sans_ecriture():
    db = FakeDB(make_session(status='CLOSED'))
    with pytest.raises(FakeHTTPException) as exc:
        close_cash(7, SimpleNamespace(declared_amount=0, notes=None), db, make_user())
    assert exc.value.status_code == 409
    assert db.add_calls == db.commit_calls == 0

def test_admin_peut_cloturer_autre_caisse():
    db = FakeDB(make_session(user_id=3))
    result = close_cash(7, SimpleNamespace(declared_amount=175, notes=None), db,
                        make_user(role='ADMIN'))
    assert result['status'] == 'CLOSED'

"""Tests statiques de la gestion de conflit d'ouverture de caisse."""
import ast
from pathlib import Path

SRC=(Path(__file__).parent/'app'/'main.py').read_text(encoding='utf-8')
TREE=ast.parse(SRC)
OPEN=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='open_cash_session')
CODE=ast.get_source_segment(SRC,OPEN)

def test_catch_integrity_and_rollback():
    assert 'except IntegrityError as exc:' in CODE
    assert 'db.rollback()' in CODE
    assert 'db.commit()' in CODE

def test_only_known_unique_constraint_becomes_409():
    assert 'ux_cash_sessions_one_open_per_user' in CODE
    assert 'status_code=409' in CODE
    assert 'raise HTTPException(' in CODE
    assert any(isinstance(n,ast.Raise) and n.exc is None for n in ast.walk(OPEN))

def test_prior_check_preserved():
    assert 'CashSession.user_id == user.id' in CODE
    assert 'CashSession.status == "OPEN"' in CODE

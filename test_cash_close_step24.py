"""Contrôles statiques du verrouillage de clôture, sans connexion DB."""
import ast
from pathlib import Path

SOURCE=(Path(__file__).parent/'app/main.py').read_text(encoding='utf-8-sig')
TREE=ast.parse(SOURCE)
ROUTE=next(n for n in TREE.body if isinstance(n,ast.FunctionDef) and n.name=='close_cash_session')
CODE=ast.get_source_segment(SOURCE,ROUTE)

def test_verrouillage_avant_lecture():
    assert '.with_for_update().first()' in CODE
    assert CODE.index('.with_for_update().first()') < CODE.index('if session.status != "OPEN"')

def test_409_sur_caisse_deja_fermee():
    assert 'status_code=409' in CODE and 'CASH_ALREADY_CLOSED' in CODE

def test_autorisation_avant_mutation():
    assert CODE.index('if session.user_id != user.id') < CODE.index('session.status = "CLOSED"')

def test_audit_et_commit_unique():
    assert CODE.count('db.commit()') == 1
    assert CODE.index('db.add(Audit(') < CODE.index('db.commit()')
    assert 'db.rollback()' in CODE

def test_aucun_verrouillage_en_dehors_route_cloture():
    assert 'with_for_update' in CODE
    assert 'with_for_update' not in SOURCE[:SOURCE.index('@app.post("/cash/sessions/{session_id}/close")')][-1000:]

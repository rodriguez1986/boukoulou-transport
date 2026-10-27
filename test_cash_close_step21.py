"""Contrôles statiques de la clôture de caisse : aucun accès base."""
import ast
from pathlib import Path

SOURCE=(Path(__file__).parent/'app'/'main.py').read_text(encoding='utf-8-sig')
TREE=ast.parse(SOURCE)

def close_source():
    for node in TREE.body:
        if not isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) or node.name!='close_cash_session':
            continue
        decorators=[ast.unparse(d) for d in node.decorator_list]
        assert any('/cash/sessions/{session_id}/close' in d and '.post(' in d for d in decorators)
        return ast.get_source_segment(SOURCE,node)
    raise AssertionError('Route de clôture introuvable')

def test_role_et_propriete():
    s=close_source()
    assert 'roles("ADMIN", "AGENT","CONTROLLER")' in s
    assert 'session.user_id != user.id and role_value != "ADMIN"' in s
    assert 'status_code=403' in s

def test_etats_invalides():
    s=close_source()
    assert 'status_code=404' in s
    assert 'session.status != "OPEN"' in s
    assert 'status_code=409' in s
    assert 'CASH_ALREADY_CLOSED' in s

def test_seules_especes_dans_montant_attendu():
    s=close_source()
    assert 'cash_revenue = recettes_par_provider.get("CASH", 0)' in s
    assert 'expected = session.opening_amount + cash_revenue' in s
    assert 'session.expected_amount = expected' in s

def test_ecart_et_cloture():
    s=close_source()
    assert 'session.declared_amount = data.declared_amount' in s
    assert 'session.difference_amount = data.declared_amount - expected' in s
    assert 'session.status = "CLOSED"' in s
    assert 'session.closed_at = datetime.now(timezone.utc)' in s

def test_commit_et_audit():
    s=close_source()
    assert 'db.commit()' in s
    assert 'action="CLOSE_CASH_SESSION"' in s
    assert s.index("db.add(Audit(") < s.index("db.commit()")

def test_rectification_conserve_montant_attendu():
    start=SOURCE.index('def rectify_cash_session(')
    end=SOURCE.index('return {',start)
    s=SOURCE[start:end]
    assert 'session.status != "CLOSED"' in s
    assert 'session.difference_amount = new_difference' in s
    assert 'session.expected_amount =' not in s

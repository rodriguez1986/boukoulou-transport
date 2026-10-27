"""Contrôles de double comptage sans connexion à une base de données."""
import ast
from pathlib import Path
from app.reconciliation_step26 import detecter_references_communes

ROOT = Path(__file__).parent


def test_reference_commune_meme_caisse_declenche_alerte():
    p = [{'reference': 'V-123', 'status': 'SUCCESS', 'amount': 5000, 'cash_session_id': 7}]
    v = [{'reference': 'V-123', 'total': 5000, 'cash_session_id': 7}]
    assert detecter_references_communes(p, v) == [{
        'reference': 'V-123', 'montant_paiement': 5000, 'montant_passe': 5000,
        'session_paiement': 7, 'session_passe': 7,
        'meme_session': True, 'meme_montant': True}]


def test_reference_commune_sessions_differentes_est_signalee():
    p = [{'reference': 'V-123', 'status': 'SUCCESS', 'amount': 5000, 'cash_session_id': 7}]
    v = [{'reference': 'V-123', 'total': 5000, 'cash_session_id': 8}]
    alertes = detecter_references_communes(p, v)
    assert len(alertes) == 1 and alertes[0]['meme_session'] is False


def test_paiement_non_valide_exclu():
    p = [{'reference': 'V-123', 'status': 'PENDING', 'amount': 5000}]
    v = [{'reference': 'V-123', 'total': 5000}]
    assert detecter_references_communes(p, v) == []


def test_references_distinctes_non_concluantes():
    p = [{'reference': 'PAY-1', 'status': 'SUCCESS', 'amount': 5000}]
    v = [{'reference': 'PASS-1', 'total': 5000}]
    assert detecter_references_communes(p, v) == []


def test_ventilation_actuelle_additionne_deux_sources():
    src = (ROOT / 'app' / 'payment_breakdown.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    assert any(isinstance(n, ast.FunctionDef) and n.name == 'calculer_recettes_par_provider' for n in tree.body)
    assert 'Payment.status == PaymentStatus.SUCCESS' in src
    assert 'Pass59.total' in src
    assert src.count('resultats[cle] = resultats.get(cle, 0) + int(montant or 0)') == 2


def test_diagnostic_ne_modifie_pas_la_base():
    tree = ast.parse((ROOT / 'app' / 'reconciliation_step26.py').read_text())
    forbidden = {'commit', 'flush', 'execute', 'add', 'delete', 'rollback'}
    assert not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in forbidden for n in ast.walk(tree))
